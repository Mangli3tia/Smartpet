import json
import threading
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT, ENCRYPTION_KEY,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS)
from database import init_db, save_sensor_data, save_alert, get_pet_type
from utils.rule_engine import evaluate
from utils.crypto import decrypt
from utils.feeder import feed
from utils.ac import ac_on, ac_off

custom_temp_humi = {}
lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("Subscriber connected to MQTT Broker")
    client.subscribe("demo/+/sensor/temp")
    client.subscribe("demo/+/sensor/humi")
    client.subscribe("demo/+/camera/alert")
    client.subscribe("custom/+/sensor/temp")
    client.subscribe("custom/+/sensor/humi")
    client.subscribe("custom/+/camera/alert")
    client.subscribe("pet/+/control/feeder")
    client.subscribe("pet/+/control/ac")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload_str = msg.payload.decode()

    # 控制指令 (topic: pet/{pet_id}/control/feeder 或 pet/{pet_id}/control/ac)
    parts = topic.split('/')
    if len(parts) == 5 and parts[2] == 'control':
        try:
            pet_id = int(parts[1])
        except:
            return
        device = parts[3]
        if device == 'feeder':
            if payload_str == "feed":
                success = feed()
                client.publish(TOPIC_FEEDER_STATUS.format(pet_id=pet_id), "success" if success else "fail")
            else:
                client.publish(TOPIC_FEEDER_STATUS.format(pet_id=pet_id), "unknown")
        elif device == 'ac':
            if payload_str == "on":
                success = ac_on()
                client.publish(TOPIC_AC_STATUS.format(pet_id=pet_id), "on" if success else "fail")
            elif payload_str == "off":
                success = ac_off()
                client.publish(TOPIC_AC_STATUS.format(pet_id=pet_id), "off" if success else "fail")
            else:
                client.publish(TOPIC_AC_STATUS.format(pet_id=pet_id), "unknown")
        return

    # 处理 Demo / Custom 宠物数据 (demo/... 或 custom/...)
    if topic.startswith("demo/") or topic.startswith("custom/"):
        try:
            payload_str = decrypt(payload_str, ENCRYPTION_KEY)
        except Exception:
            print(f"Decryption failed for {topic} — skipping")
            return
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
            ptype = get_pet_type(pet_id)
            label = "Demo" if ptype == "default" else "Own"
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
                    print(f"[{label} Pet {pet_id}] {temp}°C {humi}%")
                    alerts = evaluate(pet_id, 'temp', {'value': temp}) + evaluate(pet_id, 'humi', {'value': humi})
                    for alert in alerts:
                        save_alert(pet_id, "Environment Alert", alert)
                        print(f"[{label} Pet {pet_id}] ALERT: {alert}")
        elif len(parts) >= 4 and parts[2] == 'camera' and parts[3] == 'alert':
            try:
                pet_id = int(parts[1])
            except:
                return
            try:
                payload = json.loads(payload_str)
            except:
                return
            ptype = get_pet_type(pet_id)
            label = "Demo" if ptype == "default" else "Own"
            img_path = payload.get('image', '')
            event_time = payload.get('time', '')

            snapshot_msg = f"Snapshot at {event_time}"
            save_alert(pet_id, "Snapshot", snapshot_msg, img_path)

            alerts = evaluate(pet_id, 'camera', payload)
            for alert in alerts:
                save_alert(pet_id, "Camera Alert", alert, img_path)
                print(f"[{label} Pet {pet_id}] Camera alert: {alert}")
        return

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