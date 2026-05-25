import random
import time
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_TEMP, TOPIC_HUMI

# 连接成功回调（1.6.1 版本签名，无 properties）
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ 传感器发布端已连接到 MQTT 服务器")
    else:
        print(f"❌ 连接失败，返回码: {rc}")

# 消息发布成功回调（1.6.1 版本签名）
def on_publish(client, userdata, mid):
    print(f"✅ 消息已发布, mid={mid}")

# 创建客户端（1.6.1 直接 Client()，无参数）
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

print("传感器发布端启动，每2秒发送一次温湿度数据...\n")

try:
    while True:
        temp = round(random.uniform(15, 35), 1)
        humi = random.randint(30, 80)
        client.publish(TOPIC_TEMP, json.dumps({"value": temp}))
        client.publish(TOPIC_HUMI, json.dumps({"value": humi}))
        print(f"[传感器] 温度:{temp}°C  湿度:{humi}%")
        time.sleep(2)
except KeyboardInterrupt:
    print("\n传感器发布端已停止")
    client.loop_stop()
    client.disconnect()