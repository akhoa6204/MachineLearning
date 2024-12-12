import cv2
import threading
import time
from yolodetect import YoloDetect
# from library import *
import numpy as np
import queue
from telegram_utils import send_telegram_video
import datetime

video = cv2.VideoCapture(0)  # Mở webcam
points = []
detect = False
check = False
fps = video.get(cv2.CAP_PROP_FPS)
if fps == 0 or fps is None:
    print("FPS không hợp lệ, thiết lập lại FPS mặc định là 30")
    fps = 30

params_queue = queue.Queue()
params_queue.put({
    'recording': False
})
frame_lock = threading.Lock() 
 
video_resolution = (1280, 720)

video.set(cv2.CAP_PROP_FRAME_WIDTH, video_resolution[0])
video.set(cv2.CAP_PROP_FRAME_HEIGHT, video_resolution[1])

model = YoloDetect()

def cut_video(start_time, input_file, output_file):
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS)  # FPS của video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Tổng số khung hình trong video

    start_frame = max(int((start_time - 5) * fps) , 0)
    end_frame = total_frames  # Kết thúc là toàn bộ video từ start_time

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

def event_based_recording(video, fps, video_resolution):
    """Luồng 2: Ghi video dựa trên sự kiện"""
    print("[Luồng 2] Bắt đầu ghi dựa trên sự kiện.")
    time = 0
    segment_index = 1
    file_name = f'event_segment.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    event_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)

    while True:
        ret, frame = video.read()
        frame = cv2.flip(frame, 1)  # Lật ngược frame 
        time += 1 / fps  # Cập nhật thời gian (FPS chính xác)
        
        # Ghi video vào file hiện tại
        with frame_lock:
            event_writer.write(frame)

        # Kiểm tra điều kiện ghi video
        if not params_queue.empty():
            param = params_queue.get()
            if param.get('recording', False):  # Nếu recording = True, cắt video và bắt đầu đoạn mới
                start = time  # Lấy thời gian bắt đầu của đoạn video hiện tại
                event_writer.release()  # Dừng ghi video hiện tại
                output_file = f'event_segment_final_detect_{segment_index}.avi'
                cut_video(start, file_name, output_file)  # Cắt video từ start_time

                # Gửi video qua Telegram
                thread = threading.Thread(target=send_telegram_video, args=(output_file), daemon=True)
                thread.start()
                
                # Tăng chỉ số phân đoạn và tạo video mới
                segment_index += 1
                event_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)
                
def continuous_recording(video, fps, video_resolution):
    day = datetime.datetime.now().strftime(r'%d-%m-%Y')
    """Luồng 1: Ghi video liên tục trong 1 ngày"""
    print("[Luồng 1] Bắt đầu ghi liên tục.")
    file_name = f'daily_recording_{day}.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID') 
    day_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)

    start_time = time.time()
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        with frame_lock:
            day_writer.write(frame)  # Ghi frame vào file ngày

        # Kiểm tra nếu đã hết 24 giờ
        elapsed_time = time.time() - start_time
        if elapsed_time >= 86400:  # 86400 giây = 1 ngày
            print("[Luồng 1] Kết thúc video 24 giờ và lưu.")
            day_writer.release() 
            day = datetime.datetime.now().strftime(r'%d-%m-%Y')
            day += 1
            file_name = f'daily_recording_{day}.avi'
            day_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)
            start_time = time.time()


thread1 = threading.Thread(target=continuous_recording, args=(video, fps, video_resolution), daemon=True)
thread2 = threading.Thread(target=event_based_recording, args=(video, fps, video_resolution), daemon=True)

thread1.start()
thread2.start()

while True: 
    ret, frame = video.read()
    frame = cv2.flip(frame, 1)
    frame = draw_polygon(frame, points)
    if detect: 
        frame = model.detect(frame, points)
    
    if model.is_recording: 
        check = True
    else:
        if check: 
            check = False 
            params_queue.put({
                'recording': True
            })
            
    key = cv2.waitKey(1)
    if key == ord('q') and not model.is_recording:
        break
    elif key == ord('d'):
        if len(points) > 2:
            points.append(points[0])
            detect = True
        else:
            detect = False
    elif key == ord('e'):
        detect = False
    elif key == ord('a') and not detect:
        points = []
    
    with frame_lock:
        cv2.imshow("Intrusion Warning", frame)
    if detect:
        cv2.setMouseCallback('Intrusion Warning', lambda *args: None)
    else:
        cv2.setMouseCallback('Intrusion Warning', handle_click, points)


video.release()
cv2.destroyAllWindows()
