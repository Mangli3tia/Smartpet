import json
import threading
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS)
from database import init_db, save_sensor_data, save_alert
from utils.rule_engine import evaluate
from utils.feeder import feed
from utils.ac import ac_on, ac_off

# 缓存当前最新温湿度，按宠物存储
current_sensors = {}  # {pet_id: {'temp': None, 'humi': None}}
lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("订阅端已连接 MQTT Broker")
    # 订阅所有宠物的相关主题（通配符 +）
    client.subscribe("pet/+/sensor/temp")
    client.subscribe("pet/+/sensor/humi")
    client.subscribe("pet/+/camera/alert")
    client.subscribe("pet/+/control/feeder")
    client.subscribe("pet/+/control/ac")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload_str = msg.payload.decode()
    parts = topic.split('/')
    if len(parts) < 3:
        return
    pet_id = int(parts[1])  # 假设 pet_id 为数字
    device = parts[2]       # sensor, camera, control, status

    # 处理控制指令
    if device == 'control':
        if parts[3] == 'feeder' and payload_str == 'feed':
            success = feed()
            status_topic = TOPIC_FEEDER_STATUS.format(pet_id=pet_id)
            client.publish(status_topic, "success" if success else "fail")
        elif parts[3] == 'ac':
            if payload_str == 'on':
                success = ac_on()
                status_topic = TOPIC_AC_STATUS.format(pet_id=pet_id)
                client.publish(status_topic, "on" if success else "fail")
            elif payload_str == 'off':
                success = ac_off()
                status_topic = TOPIC_AC_STATUS.format(pet_id=pet_id)
                client.publish(status_topic, "off" if success else "fail")
        return

    # 处理传感器和摄像头数据
    try:
        payload = json.loads(payload_str)
    except:
        print(f"非 JSON 消息: {topic}")
        return

    if device == 'sensor':
        if parts[3] == 'temp':
            with lock:
                if pet_id not in current_sensors:
                    current_sensors[pet_id] = {'temp': None, 'humi': None}
                current_sensors[pet_id]['temp'] = payload['value']
        elif parts[3] == 'humi':
            with lock:
                if pet_id not in current_sensors:
                    current_sensors[pet_id] = {'temp': None, 'humi': None}
                current_sensors[pet_id]['humi'] = payload['value']
        # 当温湿度都收到时，保存并调用规则引擎
        with lock:
            data = current_sensors.get(pet_id, {})
            if data['temp'] is not None and data['humi'] is not None:
                temp = data['temp']
                humi = data['humi']
                data['temp'] = None
                data['humi'] = None
                # 保存传感器数据
                save_sensor_data(pet_id, temp, humi)
                # 分别评估温湿度
                alerts = []
                alerts.extend(evaluate(pet_id, 'temp', {'value': temp}))
                alerts.extend(evaluate(pet_id, 'humi', {'value': humi}))
                for alert in alerts:
                    save_alert(pet_id, "Environment Alert", alert)
                    print(f"[宠物{pet_id}] 规则引擎: {alert}")

    elif device == 'camera' and parts[3] == 'alert':
        event_time = payload.get('time', '')
        img_path = payload.get('image', '')
        alert_msg = evaluate(pet_id, 'camera', payload)[0]  # 获取警报文本
        save_alert(pet_id, "Camera Alert", alert_msg, img_path)
        print(f"[宠物{pet_id}] 摄像头告警: {alert_msg}")

def main():
    init_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("订阅端启动，等待消息...")
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("订阅端停止")