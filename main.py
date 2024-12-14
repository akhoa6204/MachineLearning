import cv2
import threading
from yolodetect import YoloDetect
import numpy as np
from telegram_utils import send_video_telegram_full_day
import datetime

video = cv2.VideoCapture(0)  # Mở webcam
points = []
detect = False
check = False
 
video_resolution = (640, 480)
fps = 20
video.set(cv2.CAP_PROP_FRAME_WIDTH, video_resolution[0])
video.set(cv2.CAP_PROP_FRAME_HEIGHT, video_resolution[1])

frame_lock = threading.Lock() 
frame_count = 0
model = YoloDetect()

day_writer = None
thread = None

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

def start_recording(fps, video_resolution, current_time):
    start_hour = current_time.replace(minute=0, second=0, microsecond=0)
    end_time = start_hour + datetime.timedelta(hours=1)
    print(f"Bắt đầu ghi liên tục vào {current_time.strftime(r'%d-%m-%Y-%H-%M')}")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    file_name = f'daily_recording_{start_hour.strftime(r"%d-%m-%Y")}_{current_time.strftime(r"%H-%M")}_{end_time.strftime(r"%H-%M")}.mp4'
    day_writer = cv2.VideoWriter(file_name, fourcc, fps, video_resolution)
    return file_name, day_writer, end_time
def stop_recording(day_writer):
    print("Kết thúc video 1 giờ và lưu.")
    day_writer.release()
def send_video(file_name):
    thread = threading.Thread(target=send_video_telegram_full_day, args=(file_name,))
    thread.start()
    return thread
def recording(day_writer, frame, frame_count, current_time, end_time):
    global frame_lock
    check = False
    if day_writer:
        if frame_count % 5 == 0:
            with frame_lock: 
                day_writer.write(frame)
        if current_time >= end_time: 
            check = True
    return check

while True: 
    ret, frame = video.read()
    frame = cv2.flip(frame, 1)
    frame = draw_polygon(frame, points)
    current_time = datetime.datetime.now()
    
    if not day_writer:
        file_name, day_writer, end_time = start_recording(fps, video_resolution, current_time)
    
    check = recording(day_writer, frame, frame_count, current_time, end_time)
    frame_count += 1
    
    if check: 
        stop_recording(day_writer)
        thread = send_video(file_name)
     
    if detect: 
        frame = model.detect(frame, points)
        
    key = cv2.waitKey(1)
    if key == ord('q') and not model.is_recording:
        cv2.destroyWindow("Intrusion Warning")
        stop_recording(day_writer)
        if thread:
            thread.join()
        else:
            thread = send_video(file_name)
            thread.join()
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
