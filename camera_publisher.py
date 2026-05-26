import random
import time
import json
import os
import threading
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_CAMERA, TOPIC_CAMERA_REQUEST
from PIL import Image, ImageDraw

# 确保 static 目录存在
os.makedirs("static", exist_ok=True)

def generate_random_image(event_type):
    """生成一张随机颜色的图片，并在上面绘制事件信息，返回图片文件名（相对路径）"""
    timestamp = int(time.time())
    img_name = f"snapshot_{timestamp}.jpg"
    img_path = os.path.join("static", img_name)

    # 创建随机颜色的背景
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (320, 240), color=color)
    draw = ImageDraw.Draw(img)

    # 绘制文字：事件类型和时间
    text = f"{event_type}\n{time.strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((10, 10), text, fill=(255, 255, 255))

    img.save(img_path)
    print(f"📸 已生成图片: {img_name}")
    return img_name

def on_connect(client, userdata, flags, rc):
    print("✅ 摄像头发布端已连接到 MQTT Broker")
    client.subscribe(TOPIC_CAMERA_REQUEST)

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_CAMERA_REQUEST:
        print("📸 收到手动拍照请求")
        img_name = generate_random_image("manual")
        alert_msg = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "manual_snapshot",
            "image": img_name
        }
        client.publish(TOPIC_CAMERA, json.dumps(alert_msg))
        print(f"✅ 已拍照并发布: {img_name}")

def periodic_photo():
    """每隔10秒，30%概率自动拍照并发布告警"""
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            event_type = "pet_moved"
            img_name = generate_random_image(event_type)
            alert_msg = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": event_type,
                "image": img_name
            }
            client.publish(TOPIC_CAMERA, json.dumps(alert_msg))
            print(f"🤖 自动拍照并发布告警: {img_name}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# 启动自动拍照线程
threading.Thread(target=periodic_photo, daemon=True).start()

print("摄像头发布端已启动，支持手动拍照请求")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("摄像头发布端已停止")
    client.loop_stop()