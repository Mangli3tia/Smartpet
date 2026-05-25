import json
import threading
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA, TEMP_MAX, HUMI_MIN
from database import init_db, save_sensor_data, save_alert

current_temp = None
current_humi = None
lock = threading.Lock()

def on_connect(client, userdata, flags, rc, properties=None):
    print("订阅端已连接 MQTT Broker")
    client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUMI, 0), (TOPIC_CAMERA, 0)])

def on_message(client, userdata, msg):
    global current_temp, current_humi
    topic = msg.topic
    payload = json.loads(msg.payload.decode())

    if topic == TOPIC_TEMP:
        with lock:
            current_temp = payload["value"]
    elif topic == TOPIC_HUMI:
        with lock:
            current_humi = payload["value"]
    elif topic == TOPIC_CAMERA:
        event_time = payload.get("time", "")
        img_path = payload.get("image", "")
        msg_text = f"检测到宠物活动，时间：{event_time}"
        save_alert("摄像头告警", msg_text, img_path)
        print(f"[规则引擎] 摄像头告警已保存: {msg_text}")
        return

    if current_temp is not None and current_humi is not None:
        with lock:
            temp = current_temp
            humi = current_humi
            current_temp = None
            current_humi = None

        save_sensor_data(temp, humi)
        print(f"[订阅端] 保存数据 -> 温度:{temp}°C 湿度:{humi}%")

        alerts = []
        if temp > TEMP_MAX:
            alerts.append(f"高温警报：{temp}°C 超过阈值 {TEMP_MAX}°C")
        if humi < HUMI_MIN:
            alerts.append(f"低湿警报：{humi}% 低于阈值 {HUMI_MIN}%")

        for alert_msg in alerts:
            save_alert("环境警报", alert_msg)
            print(f"[规则引擎] {alert_msg}")

def main():
    init_db()
    client = mqtt.Client()   # 修改这里
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