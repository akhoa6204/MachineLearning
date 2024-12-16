import cv2
import threading
from yolodetect import YoloDetect
import numpy as np
from telegram_utils import send_video_telegram
import datetime
import queue
import pyaudio
import wave
import pygame
import os
from time import sleep

video = cv2.VideoCapture(0)  # Mở webcam
video_resolution = (640, 480)
fps = 20
video.set(cv2.CAP_PROP_FRAME_WIDTH, video_resolution[0])
video.set(cv2.CAP_PROP_FRAME_HEIGHT, video_resolution[1])


def handle_click(event, x, y, flags, points):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
    elif event == cv2.EVENT_RBUTTONDOWN:
        for point in points:
            distance = np.sqrt((point[0] - x) ** 2 + (point[1] - y) ** 2)
            if distance < 10:
                points.remove(point)
                print(f"Xóa điểm: {point}")
                break 

def draw_polygon(frame, points):
    for point in points:
        frame = cv2.circle(frame, (point[0], point[1]), 5, (0,0,255), -1)

    frame = cv2.polylines(frame, [np.int32(points)], False, (255,0,0), thickness=2)
    return frame

def start_recording(fps, video_resolution, current_time, event):
    start_hour = current_time.replace(minute=0, second=0, microsecond=0)
    end_time = start_hour + datetime.timedelta(hours=1)
        
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    if not event:
        print(f"Bắt đầu ghi liên tục vào {current_time.strftime(r'%d-%m-%Y %H:%M')}")
        file_name = f'daily_recording_{start_hour.strftime(r"%d-%m-%Y")}_{current_time.strftime(r"%H-%M")}_{end_time.strftime(r"%H-%M")}.mp4'
    else:
        print(f"Bắt đầu ghi đối tượng xâm nhập vào {current_time.strftime(r'%d-%m-%Y %H:%M')}")
        file_name = f'event_{current_time.strftime(r"%d-%m-%Y %H-%M")}.mp4'
    day_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)

    
    return file_name, day_writer, end_time

def stop_recording(day_writer, event):
    if not event:
        print("Kết thúc video 1 giờ và lưu.")
    else:
        print("Kết thúc video quay đối tượng xâm nhập và lưu.")
    day_writer.release()
    
def send_video(file_name):
    print('Đang gửi video...')
    thread = threading.Thread(target=send_video_telegram, args=(file_name,))
    thread.start()
    return thread

def recording(day_writer, frame, frame_count, current_time, end_time, speed):
    check = False
    if day_writer:
        if frame_count % speed == 0:
            day_writer.write(frame)
        if current_time >= end_time: 
            check = True
    return check

print('''- Nhấn 'd' để hoàn thành vẽ vùng và bắt đầu detect
- Nhấn 'q' để thoát chương trình
- Nhấn 'a' để xóa toàn bộ vùng cảnh báo
- Nhấn 'e' để dừng tạm dừng theo dõi 
- Click chuột trái để chọn các điểm tạo vùng cảnh báo
- Click chuột phải để xoá điểm cảnh báo
''')
stopflag = queue.Queue()
stopflag.put(False)

stopflag_audio = queue.Queue()
stopflag_audio.put(False)

stop_alarm = False
stopflag_event = False

def start_recording_audio(current_time):
    print("[INFO] Bắt đầu ghi âm...")
    p = pyaudio.PyAudio()
    format = pyaudio.paInt16
    channels = 2
    rate = 22050
    chunk = 1024
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    start_hour = current_time.replace(minute=0, second=0, microsecond=0)
    end_time = start_hour + datetime.timedelta(hours=1)
    
    file_name = f'audio_{start_hour.strftime(r"%d-%m-%Y")}_{current_time.strftime(r"%H-%M")}_{end_time.strftime(r"%H-%M")}.wav'

    return format, channels, rate, chunk, stream, p, file_name, end_time

def stop_recording_audio(p, stream):
    print("[INFO] Dừng ghi âm.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
def recording_audio(current_time, end_time, data, frames, audio_chunk_count, speed):
    check = False
    if audio_chunk_count % speed == 0:
        frames.append(data)
    if current_time >= end_time:
        check = True
    return check

def save_audio(output_filename, channels, p, rate, frames, format):
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
def thread_record_audio():
    audio_thread = None
    audio_chunk_count = 0
    frames = []
    stream = None
    while True:
        current_time = datetime.datetime.now()
        if not stream: 
            format, channels, rate, chunk, stream, p, file_name, end_time = start_recording_audio(current_time)
            
        data = stream.read(chunk)

        check = recording_audio(current_time, end_time, data, frames, audio_chunk_count, 5)
        if check: 
            stop_recording_audio(p, stream)
            audio_thread = threading.Thread(target=save_audio, args=(file_name, channels, p, rate, frames, format,))
            audio_thread.start()
        audio_chunk_count += 1
        
        if not stopflag_audio.empty():
            if stopflag_audio.get():
                stop_recording_audio(p, stream)
                if audio_thread:
                    audio_thread.join()
                else:
                    audio_thread = threading.Thread(target=save_audio, args=(file_name, channels, p, rate, frames, format,))
                    audio_thread.start()
                    audio_thread.join()
                break

def thread_1hour(video, fps, video_resolution, stopflag): 
    frame_count = 0
    check, day_writer, thread = False, False, False
    while True: 
        ret, frame = video.read()
        frame = cv2.flip(frame, 1)
        current_time = datetime.datetime.now()
        if not day_writer:
            file_name, day_writer, end_time = start_recording(fps, video_resolution, current_time, None)
        check = recording(day_writer, frame, frame_count, current_time, end_time, 5)
        frame_count += 1
        if check: 
            stop_recording(day_writer, None)
            thread = send_video(file_name)
        if not stopflag.empty():
            if stopflag.get():
                stop_recording(day_writer, None)
                if thread:
                    thread.join()
                else:
                    thread = send_video(file_name)
                    thread.join()
                break

def cut_video(start_time, input_file, output_file):
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS) 
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) 

    start_frame = max(int((start_time - 5) * fps) , 0)
    end_frame = total_frames 

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if start_frame <= frame_count <= end_frame:
            out.write(frame)
        frame_count += 1
        if frame_count > end_frame:
            break
    cap.release()
    out.release()
    
def process_fileName(file):
    file_name = file.split('.')[0] + '_final_cut'
    file_path = file.split('.')[-1]
    return file_name + '.' + file_path

def thread_event():
    global stopflag_event, detect
    frame_count = 0
    check_moving, event_writer, thread = False, False, False
    start_time = None
    time = 0
    while True: 
        time += 1/fps
        ret, frame = video.read()
        frame = cv2.flip(frame, 1)
        current_time = datetime.datetime.now()
        if not event_writer:
            file_name, event_writer, end_time = start_recording(fps, video_resolution, current_time, True)
        recording(event_writer, frame, frame_count, current_time, end_time, 1)
        frame_count += 1
        if detect: 
            if not check_moving:
                start_time = time
            check_moving = True 
        else:
            if check_moving:
                stop_recording(event_writer, True)
                output_file = process_fileName(file_name)
                cut_video(start_time, file_name, output_file)
                os.remove(file_name)
                thread = send_video(output_file)
                check_moving = False 
                
        if stopflag_event:
            stop_recording(event_writer, True)
            if thread:
                thread.join()
            if check_moving:
                thread = send_video(file_name)
                thread.join()
            break
        
        
pass
def play_alarm(path_sound=r'alarm-alert-sound-effect-230557.mp3'):
    global stop_alarm
    try:
        if os.path.exists(path_sound):
            pygame.mixer.init()
            pygame.mixer.music.load(path_sound)

            while not stop_alarm:
                pygame.mixer.music.play(2)
                sleep(5)# Giữ cho luồng chạy mà không bị chặn
            pygame.mixer.music.stop()  # Dừng âm thanh khi cần
        else:
            print(f"File âm thanh không tồn tại: {path_sound}")
    except Exception as e:
        print(f"Lỗi: {e}")

        

points = []
detect = False
model = YoloDetect()
thread_record_1hour = threading.Thread(target=thread_1hour, args=[video, fps, video_resolution, stopflag,])
thread_audio = threading.Thread(target=thread_record_audio)
thread_event_detect = threading.Thread(target=thread_event)
thread_alarm = None

thread_record_1hour.start()
thread_audio.start()
thread_event_detect.start()
while True: 
    ret, frame = video.read()
    frame = cv2.flip(frame, 1)
    frame = draw_polygon(frame, points)
    
    if detect: 
        frame = model.detect(frame, points)
        if not thread_alarm:
            stop_alarm = False
            thread_alarm = threading.Thread(target=play_alarm)
            thread_alarm.start()
    else:
        if thread_alarm:
            stop_alarm = True
            
    key = cv2.waitKey(1)
    if key == ord('q'):
        cv2.destroyWindow("Intrusion Warning")
        stopflag.put(True)
        stopflag_audio.put(True)
        stop_alarm = True
        stopflag_event = True 
        
        thread_record_1hour.join()
        thread_audio.join()
        break
    elif key == ord('d'):
        if len(points) > 2:
            points.append(points[0])
            detect = True
        else:
            detect = False
    elif key == ord('e'):
        detect = False
    elif key == ord('a'):
        points = []
    

    cv2.imshow("Intrusion Warning", frame)
    
    if detect:
        cv2.setMouseCallback('Intrusion Warning', lambda *args: None)
    else:
        cv2.setMouseCallback('Intrusion Warning', handle_click, points)

video.release()
cv2.destroyAllWindows()



# # Kết hợp video và âm thanh
# def combine_audio_video(video_file, audio_file, output_file):
#     print("[INFO] Đang kết hợp video và âm thanh...")
#     video_clip = VideoFileClip(video_file)
#     audio_clip = AudioFileClip(audio_file)
#     final_clip = video_clip.set_audio(audio_clip)
#     final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
#     print("[INFO] Hoàn tất kết hợp!")



