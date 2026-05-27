import time
import threading
import random
import json
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT, 
                    TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA, TOPIC_CAMERA_REQUEST)
from utils.sensor_emulator import generate_sensor_data, format_temp_payload, format_humi_payload
from utils.camera_emulator import generate_random_image, create_alert_message

# ---------- MQTT 客户端 ----------
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def on_connect(client, userdata, flags, rc):
    print("统一发布端已连接 MQTT Broker")
    client.subscribe(TOPIC_CAMERA_REQUEST)   # 订阅手动拍照请求

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_CAMERA_REQUEST:
        print("📸 收到手动拍照请求")
        img_name = generate_random_image("manual")
        alert_msg = create_alert_message("manual_snapshot", img_name)
        client.publish(TOPIC_CAMERA, json.dumps(alert_msg),qos=1)
        print(f"✅ 手动拍照并发布: {img_name}")

client.on_connect = on_connect
client.on_message = on_message

# ---------- 温湿度发布线程 ----------
def publish_sensor():
    while True:
        temp, humi = generate_sensor_data()
        client.publish(TOPIC_TEMP, format_temp_payload(temp),qos=0)
        client.publish(TOPIC_HUMI, format_humi_payload(humi),qos=0)
        print(f"[传感器] 温度:{temp}°C  湿度:{humi}%")
        time.sleep(2)

# ---------- 摄像头自动拍照线程 ----------
def publish_camera_auto():
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            img_name = generate_random_image("pet_moved")
            alert_msg = create_alert_message("pet_moved", img_name)
            client.publish(TOPIC_CAMERA, json.dumps(alert_msg),qos=1)
            print(f"🤖 自动拍照并发布: {img_name}")

# 启动线程
threading.Thread(target=publish_sensor, daemon=True).start()
threading.Thread(target=publish_camera_auto, daemon=True).start()

print("统一发布端已启动（温湿度 + 摄像头）")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("统一发布端停止")
    client.loop_stop()