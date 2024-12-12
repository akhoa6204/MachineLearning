import requests
import os

def send_telegram_photo(img_file):
    try:
        # Thông tin cơ bản
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        # Kiểm tra và gửi ảnh
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
            print("Không tìm thấy file alert.png")
            
    except Exception as ex:
        print("Lỗi:", str(ex))
        
import requests
import os

def send_telegram_video(video_file):
    try:
        # Thông tin cơ bản
        api_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        # Kiểm tra và gửi video
        if os.path.exists(video_file):
            with open(video_file, 'rb') as video:
                response = requests.post(
                    api_url,
                    files={'video': video},
                    data={
                        'chat_id': chat_id,
                        'caption': "⚠️ Phát hiện xâm nhập!"
                    }
                )
            print("Gửi video " + ("thành công!" if response.status_code == 200 else "thất bại!"))
        else:
            print(f"Không tìm thấy file {video_file}")
            
    except Exception as ex:
        print("Lỗi:", str(ex))
