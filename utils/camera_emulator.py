import random
import time
import os
from PIL import Image, ImageDraw

# 确保 static 目录存在
os.makedirs("static", exist_ok=True)

def generate_random_image(event_type):
    """生成随机图片并返回文件名（相对路径，不含 static/）"""
    timestamp = int(time.time())
    img_name = f"snapshot_{timestamp}.jpg"
    img_path = os.path.join("static", img_name)
    # 随机背景色
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (320, 240), color=color)
    draw = ImageDraw.Draw(img)
    text = f"{event_type}\n{time.strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((10, 10), text, fill=(255, 255, 255))
    img.save(img_path)
    return img_name

def create_alert_message(event_type, img_name):
    """构造摄像头告警的 JSON 消息"""
    return {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "image": img_name
    }