import requests
import os
import datetime

def send_photo_telegram(img_file):
    try:
        bot_token = "7891478750:AAGEElm0zdy5YnjDt1f2Zv9cbbIzl1k7oF4"
        chat_id = "-4713104225"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        time = datetime.datetime.now()
        time = time.strftime(r'%Y-%m-%d %H:%M')
        if os.path.exists(img_file):
            with open(img_file, 'rb') as photo:
                response = requests.post(
                    api_url,
                    files={'photo': photo},
                    data={
                        'chat_id': chat_id,
                        'caption': f"⚠️ Phát hiện xâm nhập vào {time}!"
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
        time = ' '.join(video_path.split('_')[2:]).replace('.mp4', '')
        if os.path.exists(video_path):
            with open(video_path, 'rb') as video:
                response = requests.post(
                    api_url,
                    files={'video': video},
                    data={
                        'chat_id': chat_id,
                        'caption': f"{time}"
                    }
                )
            print(f"Gửi video {video_path} " + ("thành công!" if response.status_code == 200 else "thất bại!"))
            os.remove(video_path)
        else:
            print("Không tìm thấy file video:", video_path)

    except Exception as ex:
        print("Lỗi:", str(ex))
        
