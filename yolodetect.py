from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import cv2
from telegram_utils import send_photo_telegram
import datetime
from ultralytics import YOLO
import threading


def isInside(points, centroid):
    polygon = Polygon(points)
    centroid = Point(centroid)
    print(polygon.contains(centroid))
    return polygon.contains(centroid)


class YoloDetect():
    def __init__(self, detect_class="person", frame_width=1280, frame_height=720):
        # Parameters
        self.detect_class = detect_class
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.conf_threshold = 0.5
        # Load YOLOv8 model
        self.model = YOLO('yolov8n.pt')  # or 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'
        self.last_alert = None
        self.alert_telegram_each = 15  # seconds

    def alert(self, img):
        cv2.putText(img, "ALARM!!!!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # New thread to send telegram after 15 seconds
        if (self.last_alert is None) or (
                (datetime.datetime.now() - self.last_alert).total_seconds() > self.alert_telegram_each):
            self.last_alert = datetime.datetime.now()
            cv2.imwrite("alert.png", img)
            img_file = "alert.png"
            thread = threading.Thread(target=send_photo_telegram, args =[img_file, self.last_alert, ])
            thread.start()
            thread.join()

        return img        

    def detect(self, frame, points):
        # Thực hiện detect với YOLOv8
        results = self.model(frame, conf=self.conf_threshold)
        for result in results[0]:
            boxes = result.boxes
            for box in boxes:
                # Lấy tọa độ box
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Lấy class name
                cls = int(box.cls[0])
                class_name = self.model.names[cls]
                
                # Chỉ xử lý nếu là class cần detect (person)
                if class_name == self.detect_class:
                    # Vẽ box và label
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    # Tính toán centroid
                    centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                    cv2.circle(frame, centroid, 5, color, -1)
                    
                    # Kiểm tra xâm nhập
                    if isInside(points, centroid):
                        frame = self.alert(frame)
                        self.last_alert = datetime.datetime.utcnow()

        return frame