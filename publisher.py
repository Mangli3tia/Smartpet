import random
import time
import threading
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA, TOPIC_CAMERA_REQUEST
from utils.camera_emulator import generate_random_image, create_alert_message
from database import get_pets

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# 订阅所有宠物的拍照请求
def on_connect(client, userdata, flags, rc):
    print("发布端已连接 MQTT Broker")
    # 订阅通配符主题：pet/+/camera/request
    client.subscribe("pet/+/camera/request")

def on_message(client, userdata, msg):
    # 解析 pet_id
    topic_parts = msg.topic.split('/')
    if len(topic_parts) >= 3 and topic_parts[2] == 'camera' and topic_parts[3] == 'request':
        pet_id = topic_parts[1]
        print(f"收到手动拍照请求，pet_id={pet_id}")
        img_name = generate_random_image("manual")
        alert_msg = create_alert_message("manual_snapshot", img_name)
        # 发布到该宠物的摄像头告警主题
        camera_topic = TOPIC_CAMERA.format(pet_id=pet_id)
        client.publish(camera_topic, json.dumps(alert_msg), qos=1)
        print(f"已为宠物 {pet_id} 拍照并发布")

client.on_connect = on_connect
client.on_message = on_message

def publish_sensor_for_pet(pet_id):
    """为单个宠物持续发布温湿度数据"""
    while True:
        temp = round(random.uniform(15, 35), 1)
        humi = random.randint(30, 80)
        temp_topic = TOPIC_TEMP.format(pet_id=pet_id)
        humi_topic = TOPIC_HUMI.format(pet_id=pet_id)
        client.publish(temp_topic, json.dumps({"value": temp}))
        client.publish(humi_topic, json.dumps({"value": humi}))
        print(f"[宠物{pet_id}] 温度:{temp}°C 湿度:{humi}%")
        time.sleep(2)

def publish_camera_for_pet(pet_id):
    """为单个宠物模拟自动拍照（每10秒30%概率）"""
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            img_name = generate_random_image("pet_moved")
            alert_msg = create_alert_message("pet_moved", img_name)
            camera_topic = TOPIC_CAMERA.format(pet_id=pet_id)
            client.publish(camera_topic, json.dumps(alert_msg), qos=1)
            print(f"[宠物{pet_id}] 自动拍照并发布")

if __name__ == "__main__":
    pets = get_pets()
    if not pets:
        print("未找到宠物，请先运行 web_server.py 初始化数据库")
        exit(1)
    for pet in pets:
        pet_id = pet['id']
        threading.Thread(target=publish_sensor_for_pet, args=(pet_id,), daemon=True).start()
        threading.Thread(target=publish_camera_for_pet, args=(pet_id,), daemon=True).start()
    print(f"已为 {len(pets)} 个宠物启动发布线程")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()