import random
import time
import threading
import json
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT, ENCRYPTION_KEY,
                    TOPIC_TEMP_DEFAULT, TOPIC_HUMI_DEFAULT, TOPIC_CAMERA_DEFAULT,
                    TOPIC_TEMP_CUSTOM, TOPIC_HUMI_CUSTOM, TOPIC_CAMERA_CUSTOM,
                    TOPIC_CAMERA_REQUEST, TOPIC_SYSTEM_PET_CREATED)
from utils.sensor_emulator import generate_sensor_data as sim_sensor
from utils.camera_emulator import generate_random_image as sim_camera, create_alert_message as sim_alert
from utils.crypto import encrypt
from database import get_all_pets

# 真实硬件模块是可选的，仅在树莓派等设备上可用
try:
    from utils.real_sensor import generate_sensor_data as real_sensor
except ImportError:
    real_sensor = None
    print("⚠ real_sensor not available (requires board + adafruit_dht)")

try:
    from utils.real_camera import capture_image as real_camera, create_alert_message as real_alert
except ImportError:
    real_camera = None
    real_alert = None
    print("⚠ real_camera not available (requires cv2)")

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def pub(topic, payload, qos=0):
    """Publish encrypted payload to MQTT topic."""
    client.publish(topic, encrypt(payload, ENCRYPTION_KEY), qos)

active_pet_threads = set()
thread_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("Publisher connected")
    client.subscribe("pet/+/camera/request")
    client.subscribe(TOPIC_SYSTEM_PET_CREATED)

def on_message(client, userdata, msg):
    topic = msg.topic
    if topic == TOPIC_SYSTEM_PET_CREATED:
        pet_id = int(msg.payload.decode())
        print(f"Received new pet creation: {pet_id}")
        pets = get_all_pets()
        pet = next((p for p in pets if p['id'] == pet_id), None)
        if pet and pet['id'] not in active_pet_threads:
            with thread_lock:
                if pet['id'] not in active_pet_threads:
                    print(f"Starting thread for new pet {pet_id}")
                    t = threading.Thread(target=publish_for_pet, args=(pet,), daemon=True)
                    t.start()
                    active_pet_threads.add(pet['id'])
        return
    parts = topic.split('/')
    if len(parts) >= 3 and parts[2] == 'camera' and parts[3] == 'request':
        pet_id = parts[1]
        print(f"Manual camera request for {pet_id}")
        pets = get_all_pets()
        pet = next((p for p in pets if p['id'] == int(pet_id)), None)
        if not pet: return
        if pet['type'] == 'default':
            img = sim_camera("manual")
            alert = sim_alert("manual_snapshot", img)
            cam_topic = TOPIC_CAMERA_DEFAULT.format(pet_id=pet_id)
        else:
            if real_camera is None:
                print(f"Manual camera request for pet {pet_id} skipped — no hardware")
                return
            img = real_camera(device_id=pet.get('camera_id', 2))
            if img is None:
                print("Camera capture failed")
                return
            alert = real_alert("manual_snapshot", img)
            cam_topic = TOPIC_CAMERA_CUSTOM.format(pet_id=pet_id)
        pub(cam_topic, json.dumps(alert), qos=1)
        print(f"Published manual snapshot for {pet_id}")

client.on_connect = on_connect
client.on_message = on_message

def publish_for_pet(pet):
    pid = pet['id']
    ptype = pet['type']
    last_photo = 0
    if ptype == 'default':
        while True:
            t, h = sim_sensor()
            pub(TOPIC_TEMP_DEFAULT.format(pet_id=pid), json.dumps({"value": t}))
            pub(TOPIC_HUMI_DEFAULT.format(pet_id=pid), json.dumps({"value": h}))
            print(f"[Demo {pid}] Simulated {t}°C {h}%")
            now = time.time()
            if now - last_photo >= 10:
                img = sim_camera("auto")
                if img:
                    alert = sim_alert("auto_snapshot", img)
                    pub(TOPIC_CAMERA_DEFAULT.format(pet_id=pid), json.dumps(alert), qos=1)
                    print(f"[Demo {pid}] Auto snapshot")
                last_photo = now
            time.sleep(2)
    else:
        if real_sensor is None or real_camera is None:
            # 硬件模块不可用，Own Pet 模式不启动（不使用模拟数据）
            print(f"[Own {pid}] Hardware not available — pet requires real sensors. Skipping.")
            return
        temp_id = pet.get('temp_sensor_id', 1)
        cam_id = pet.get('camera_id', 2)
        print(f"[Own {pid}] Real hardware: sensor {temp_id}, camera {cam_id}")
        while True:
            t, h = real_sensor(device_id=temp_id)
            if t is not None and h is not None:
                pub(TOPIC_TEMP_CUSTOM.format(pet_id=pid), json.dumps({"value": t}))
                pub(TOPIC_HUMI_CUSTOM.format(pet_id=pid), json.dumps({"value": h}))
                print(f"[Own {pid}] Real data: {t}°C {h}%")
            else:
                print(f"[Own {pid}] Sensor read failed")
            now = time.time()
            if now - last_photo >= 60:
                img = real_camera(device_id=cam_id)
                if img:
                    alert = real_alert("auto_snapshot", img)
                    pub(TOPIC_CAMERA_CUSTOM.format(pet_id=pid), json.dumps(alert), qos=1)
                    print(f"[Own {pid}] Auto snapshot")
                last_photo = now
            time.sleep(2)

if __name__ == "__main__":
    pets = get_all_pets()
    for pet in pets:
        with thread_lock:
            if pet['id'] not in active_pet_threads:
                threading.Thread(target=publish_for_pet, args=(pet,), daemon=True).start()
                active_pet_threads.add(pet['id'])
    # 定期扫描新宠物
    def scanner():
        while True:
            time.sleep(10)
            current = get_all_pets()
            with thread_lock:
                for pet in current:
                    if pet['id'] not in active_pet_threads:
                        print(f"Scanner found new pet {pet['id']}, starting thread")
                        t = threading.Thread(target=publish_for_pet, args=(pet,), daemon=True)
                        t.start()
                        active_pet_threads.add(pet['id'])
    threading.Thread(target=scanner, daemon=True).start()
    print(f"Started {len(active_pet_threads)} threads")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()