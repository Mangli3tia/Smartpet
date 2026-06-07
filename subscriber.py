import json
import threading
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_TEMP_DEFAULT, TOPIC_HUMI_DEFAULT, TOPIC_CAMERA_DEFAULT,
                    TOPIC_TEMP_CUSTOM, TOPIC_HUMI_CUSTOM, TOPIC_CAMERA_CUSTOM,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS)
from database import init_db, save_sensor_data, save_alert, get_pets_by_type
from utils.rule_engine import evaluate
from utils.feeder import feed
from utils.ac import ac_on, ac_off

default_temp = None
default_humi = None
custom_temp_humi = {}
lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("Subscriber connected to MQTT Broker")
    client.subscribe([(TOPIC_TEMP_DEFAULT, 0), (TOPIC_HUMI_DEFAULT, 0), (TOPIC_CAMERA_DEFAULT, 0)])
    client.subscribe("custom/+/sensor/temp")
    client.subscribe("custom/+/sensor/humi")
    client.subscribe("custom/+/camera/alert")
    client.subscribe([(TOPIC_FEEDER, 0), (TOPIC_AC, 0)])

def on_message(client, userdata, msg):
    global default_temp, default_humi
    topic = msg.topic
    payload_str = msg.payload.decode()

    # 控制指令
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

    # 处理自定义宠物数据 (custom/...)
    if topic.startswith("custom/"):
        parts = topic.split('/')
        if len(parts) >= 4 and parts[2] == 'sensor':
            try:
                pet_id = int(parts[1])
            except:
                return
            sensor_type = parts[3]
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
                if (custom_temp_humi[pet_id]['temp'] is not None and
                    custom_temp_humi[pet_id]['humi'] is not None):
                    temp = custom_temp_humi[pet_id]['temp']
                    humi = custom_temp_humi[pet_id]['humi']
                    custom_temp_humi[pet_id] = {'temp': None, 'humi': None}
                    save_sensor_data(pet_id, temp, humi)
                    alerts = evaluate(pet_id, 'temp', {'value': temp}) + evaluate(pet_id, 'humi', {'value': humi})
                    for alert in alerts:
                        save_alert(pet_id, "Environment Alert", alert)
                        print(f"[Own Pet {pet_id}] Rule triggered: {alert}")
        elif len(parts) >= 4 and parts[2] == 'camera' and parts[3] == 'alert':
            try:
                pet_id = int(parts[1])
            except:
                return
            try:
                payload = json.loads(payload_str)
            except:
                return
            img_path = payload.get('image', '')
            event_time = payload.get('time', '')

            # ★ 无条件保存快照，用于立即更新前端图片 ★
            snapshot_msg = f"Snapshot at {event_time}"
            save_alert(pet_id, "Snapshot", snapshot_msg, img_path)
            print(f"[Own Pet {pet_id}] Snapshot saved for image update")

            # 规则引擎产生真正的告警（长时间静止等）
            alerts = evaluate(pet_id, 'camera', payload)
            for alert in alerts:
                save_alert(pet_id, "Camera Alert", alert, img_path)
                print(f"[Own Pet {pet_id}] Camera alert: {alert}")
        return

    # 处理默认宠物数据（原有主题）
    try:
        payload = json.loads(payload_str)
    except:
        print(f"Non-JSON message: {topic}")
        return

    if topic == TOPIC_TEMP_DEFAULT:
        with lock:
            default_temp = payload["value"]
    elif topic == TOPIC_HUMI_DEFAULT:
        with lock:
            default_humi = payload["value"]
    elif topic == TOPIC_CAMERA_DEFAULT:
        default_pets = get_pets_by_type('default')
        for pet in default_pets:
            # 无条件快照
            snapshot_msg = f"Snapshot at {payload.get('time', '')}"
            save_alert(pet['id'], "Snapshot", snapshot_msg, payload.get('image', ''))
            # 规则引擎告警（随机30%）
            alerts = evaluate(pet['id'], 'camera', payload)
            for alert in alerts:
                save_alert(pet['id'], "Camera Alert", alert, payload.get('image', ''))
                print(f"[Demo Pet {pet['id']}] Camera alert: {alert}")
        print("Camera snapshot and alerts processed for default pets")
        return

    if default_temp is not None and default_humi is not None:
        with lock:
            temp = default_temp
            humi = default_humi
            default_temp = None
            default_humi = None
        default_pets = get_pets_by_type('default')
        for pet in default_pets:
            save_sensor_data(pet['id'], temp, humi)
            alerts = evaluate(pet['id'], 'temp', {'value': temp}) + evaluate(pet['id'], 'humi', {'value': humi})
            for alert in alerts:
                save_alert(pet['id'], "Environment Alert", alert)
                print(f"[Demo Pet {pet['id']}] Rule triggered: {alert}")

def main():
    init_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Subscriber started, waiting for messages...")
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSubscriber stopped")