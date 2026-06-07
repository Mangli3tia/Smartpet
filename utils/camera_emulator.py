import random
import time
import os
from PIL import Image, ImageDraw

os.makedirs("static", exist_ok=True)

def generate_random_image(event_type):
    timestamp = int(time.time())
    img_name = f"snapshot_{timestamp}.jpg"
    img_path = os.path.join("static", img_name)
    color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    img = Image.new('RGB', (320,240), color=color)
    draw = ImageDraw.Draw(img)
    text = f"{event_type}\n{time.strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((10,10), text, fill=(255,255,255))
    img.save(img_path)
    return img_name

def create_alert_message(event_type, img_name):
    return {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "image": img_name
    }