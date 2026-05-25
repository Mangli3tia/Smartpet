import random
import time
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_CAMERA

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ 摄像头发布端已连接到 MQTT 服务器")
    else:
        print(f"❌ 连接失败，返回码: {rc}")

def on_publish(client, userdata, mid):
    print(f"✅ 摄像头消息已发布, mid={mid}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

print("摄像头发布端启动，每10秒有30%概率模拟宠物移动...\n")

try:
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            img_name = f"snapshot_{int(time.time())}.jpg"
            alert_msg = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "pet_moved",
                "image": img_name
            }
            client.publish(TOPIC_CAMERA, json.dumps(alert_msg))
            print(f"[摄像头] 检测到宠物移动，拍照 {img_name}")
except KeyboardInterrupt:
    print("\n摄像头发布端已停止")
    client.loop_stop()
    client.disconnect()