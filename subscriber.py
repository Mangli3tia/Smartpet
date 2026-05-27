import json
import threading
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_TEMP, TOPIC_HUMI, TOPIC_CAMERA,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS,
                    TEMP_MAX, HUMI_MIN)
from database import init_db, save_sensor_data, save_alert
from utils.feeder import feed          # 喂食器控制函数
from utils.ac import ac_on, ac_off     # 空调控制函数

current_temp = None
current_humi = None
lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print("订阅端已连接 MQTT Broker")
    client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUMI, 0), (TOPIC_CAMERA, 1),
                      (TOPIC_FEEDER, 0), (TOPIC_AC, 0)])

def on_message(client, userdata, msg):
    global current_temp, current_humi
    topic = msg.topic
    payload_str = msg.payload.decode()

    # ---------- 处理控制指令（纯文本） ----------
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

    # ---------- 处理传感器和摄像头数据（JSON） ----------
    try:
        payload = json.loads(payload_str)
    except:
        print(f"收到非 JSON 消息，忽略: {topic}")
        return

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
        print(f"[规则引擎] 摄像头告警已保存：{msg_text}")
        return

    # 当温湿度都到达时，保存并执行规则
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