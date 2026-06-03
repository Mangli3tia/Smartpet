import json
import threading
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS)
from database import init_db, save_sensor_data, save_alert, get_default_pets, get_pet_thresholds
from utils.rule_engine import evaluate
from utils.feeder import feed
from utils.ac import ac_on, ac_off

# 用于缓存默认宠物的温湿度（成对）
default_temp = None
default_humi = None
# 用于缓存自定义宠物的温湿度
custom_temp_humi = {}
lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("订阅端已连接 MQTT Broker")
    # 订阅原有主题（默认宠物使用）
    client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUMI, 0), (TOPIC_CAMERA, 0),
                      (TOPIC_FEEDER, 0), (TOPIC_AC, 0)])
    # 订阅自定义宠物主题
    client.subscribe("custom/+/sensor/temp")
    client.subscribe("custom/+/sensor/humi")

def on_message(client, userdata, msg):
    global default_temp, default_humi
    topic = msg.topic
    payload_str = msg.payload.decode()

    # ---------- 处理控制指令 ----------
    if topic == TOPIC_FEEDER:
        if payload_str == "feed":
            success = feed()
            client.publish(TOPIC_FEEDER_STATUS, "success" if success else "fail")
        else:
            client.publish(TOPIC_FEEDER_STATUS, "unknown")
        return

    if topic == TOPIC_AC:
        if payload_str == "on":
            success = ac_on()
            client.publish(TOPIC_AC_STATUS, "on" if success else "fail")
        elif payload_str == "off":
            success = ac_off()
            client.publish(TOPIC_AC_STATUS, "off" if success else "fail")
        else:
            client.publish(TOPIC_AC_STATUS, "unknown")
        return

    # ---------- 处理自定义宠物数据（主题：custom/{pet_id}/sensor/temp 或 /humi） ----------
    if topic.startswith("custom/"):
        parts = topic.split('/')
        if len(parts) >= 4 and parts[2] == 'sensor':
            try:
                pet_id = int(parts[1])
            except:
                return
            sensor_type = parts[3]  # 'temp' 或 'humi'
            try:
                payload = json.loads(payload_str)
            except:
                return
            with lock:
                if pet_id not in custom_temp_humi:
                    custom_temp_humi[pet_id] = {'temp': None, 'humi': None}
                if sensor_type == 'temp':
                    custom_temp_humi[pet_id]['temp'] = payload['value']
                elif sensor_type == 'humi':
                    custom_temp_humi[pet_id]['humi'] = payload['value']
                # 当两者都收到时，保存并触发规则
                if (custom_temp_humi[pet_id]['temp'] is not None and
                    custom_temp_humi[pet_id]['humi'] is not None):
                    temp = custom_temp_humi[pet_id]['temp']
                    humi = custom_temp_humi[pet_id]['humi']
                    custom_temp_humi[pet_id] = {'temp': None, 'humi': None}
                    # 存入数据库
                    save_sensor_data(pet_id, temp, humi)
                    # 规则引擎
                    alerts = []
                    alerts.extend(evaluate(pet_id, 'temp', {'value': temp}))
                    alerts.extend(evaluate(pet_id, 'humi', {'value': humi}))
                    for alert in alerts:
                        save_alert(pet_id, "Environment Alert", alert)
                        print(f"[自定义宠物 {pet_id}] 规则引擎: {alert}")
        return

    # ---------- 处理默认宠物数据（原有主题，无 pet_id） ----------
    try:
        payload = json.loads(payload_str)
    except:
        print(f"非 JSON 消息: {topic}")
        return

    if topic == TOPIC_TEMP:
        with lock:
            default_temp = payload["value"]
    elif topic == TOPIC_HUMI:
        with lock:
            default_humi = payload["value"]
    elif topic == TOPIC_CAMERA:
        event_time = payload.get("time", "")
        img_path = payload.get("image", "")
        msg_text = f"检测到宠物活动，时间：{event_time}"
        # 为每个默认宠物保存告警
        default_pets = get_default_pets()
        for pet in default_pets:
            save_alert(pet['id'], "摄像头告警", msg_text, img_path)
        print(f"[规则引擎] 摄像头告警已保存")
        return

    # 当默认宠物的温湿度都到达时，为每个默认宠物保存数据
    if default_temp is not None and default_humi is not None:
        with lock:
            temp = default_temp
            humi = default_humi
            default_temp = None
            default_humi = None
        default_pets = get_default_pets()
        for pet in default_pets:
            save_sensor_data(pet['id'], temp, humi)
            alerts = []
            alerts.extend(evaluate(pet['id'], 'temp', {'value': temp}))
            alerts.extend(evaluate(pet['id'], 'humi', {'value': humi}))
            for alert in alerts:
                save_alert(pet['id'], "环境警报", alert)
                print(f"[默认宠物 {pet['id']}] 规则引擎: {alert}")

def main():
    init_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("订阅端开始运行，等待 MQTT 消息...")
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n订阅端已停止")