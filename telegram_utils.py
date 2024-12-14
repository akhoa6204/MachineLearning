import requests
import os
from multiprocessing import Process

def send_photo_telegram(img_file):
    try:
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        if os.path.exists(img_file):
            with open(img_file, 'rb') as photo:
                response = requests.post(
                    api_url,
                    files={'photo': photo},
                    data={
                        'chat_id': chat_id,
                        'caption': "⚠️ Phát hiện xâm nhập!"
                    }
                )
            print("Gửi cảnh báo " + ("thành công!" if response.status_code == 200 else "thất bại!"))
        else:
            print(f"Không tìm thấy file {img_file}")
            
    except Exception as ex:
        print("Lỗi:", str(ex))
        
def send_video_telegram(video_path):
    try:
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        if os.path.exists(video_path):
            with open(video_path, 'rb') as video:
                response = requests.post(
                    api_url,
                    files={'video': video},
                    data={
                        'chat_id': chat_id,
                        'caption': "⚠️ Phát hiện xâm nhập! Video ghi lại 5 giây trước và sau sự kiện."
                    }
                )
            print("Gửi video cảnh báo " + ("thành công!" if response.status_code == 200 else "thất bại!"))
        else:
            print("Không tìm thấy file video:", video_path)

    except Exception as ex:
        print("Lỗi:", str(ex))
        
def send_video_telegram_full_day(video_path):
    try:
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        if os.path.exists(video_path):
            with open(video_path, 'rb') as video:
                response = requests.post(
                    api_url,
                    files={'video': video},
                    data={
                        'chat_id': chat_id,
                        'caption': "Gửi video toàn bộ sự việc 1 ngày !!!"
                    }
                )
            print("Gửi video toàn bộ 1 ngày " + ("thành công!" if response.status_code == 200 else "thất bại!"))
        else:
            print("Không tìm thấy file video:", video_path)

    except Exception as ex:
        print("Lỗi:", str(ex))
        
        