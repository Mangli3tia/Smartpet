import random
import time
import threading
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA, TOPIC_CAMERA_REQUEST
from utils.sensor_emulator import generate_sensor_data   # 导入温湿度模拟函数
from utils.camera_emulator import generate_random_image, create_alert_message
from database import get_pets

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def on_connect(client, userdata, flags, rc):
    print("发布端已连接 MQTT Broker")
    # 订阅手动拍照请求（兼容原有主题格式）
    client.subscribe("pet/+/camera/request")

def on_message(client, userdata, msg):
    topic_parts = msg.topic.split('/')
    if len(topic_parts) >= 3 and topic_parts[2] == 'camera' and topic_parts[3] == 'request':
        pet_id = topic_parts[1]
        print(f"收到手动拍照请求，pet_id={pet_id}")
        img_name = generate_random_image("manual")
        alert_msg = create_alert_message("manual_snapshot", img_name)
        # 获取宠物类型，决定发布主题
        pets = get_pets()
        pet = next((p for p in pets if p['id'] == int(pet_id)), None)
        if pet and pet['type'] == 'default':
            camera_topic = TOPIC_CAMERA   # 默认宠物使用旧主题（不带 pet_id）
        else:
            camera_topic = f"custom/{pet_id}/camera/alert"
        client.publish(camera_topic, json.dumps(alert_msg), qos=1)
        print(f"已为宠物 {pet_id} 拍照并发布")

client.on_connect = on_connect
client.on_message = on_message

def publish_sensor_for_pet(pet):
    """为单个宠物持续发布温湿度数据（使用 sensor_emulator）"""
    pet_id = pet['id']
    is_default = (pet['type'] == 'default')
    while True:
        temp, humi = generate_sensor_data()   # 调用外部模拟函数
        if is_default:
            temp_topic = TOPIC_TEMP
            humi_topic = TOPIC_HUMI
        else:
            temp_topic = f"custom/{pet_id}/sensor/temp"
            humi_topic = f"custom/{pet_id}/sensor/humi"
        client.publish(temp_topic, json.dumps({"value": temp}))
        client.publish(humi_topic, json.dumps({"value": humi}))
        print(f"[{'默认' if is_default else '自定义'}宠物 {pet_id}] 温度:{temp}°C 湿度:{humi}%")
        time.sleep(2)

def publish_camera_for_pet(pet):
    """为单个宠物模拟自动拍照（每10秒30%概率）"""
    pet_id = pet['id']
    is_default = (pet['type'] == 'default')
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            img_name = generate_random_image("pet_moved")
            alert_msg = create_alert_message("pet_moved", img_name)
            if is_default:
                camera_topic = TOPIC_CAMERA
            else:
                camera_topic = f"custom/{pet_id}/camera/alert"
            client.publish(camera_topic, json.dumps(alert_msg), qos=1)
            print(f"[{'默认' if is_default else '自定义'}宠物 {pet_id}] 自动拍照并发布")

if __name__ == "__main__":
    pets = get_pets()
    if not pets:
        print("未找到宠物，请先运行 web_server.py 初始化数据库")
        exit(1)
    for pet in pets:
        threading.Thread(target=publish_sensor_for_pet, args=(pet,), daemon=True).start()
        threading.Thread(target=publish_camera_for_pet, args=(pet,), daemon=True).start()
    print(f"已为 {len(pets)} 个宠物启动发布线程")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()