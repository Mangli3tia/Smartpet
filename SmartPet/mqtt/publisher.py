import time
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT, PUB_TOPIC_PREFIX
from mqtt.pet_pair import pet_list

# 连接成功回调
def on_connect(client, userdata, flags, rc):
    print("✅ 已连接到 MQTT 服务器")

# 消息发布成功回调
def on_publish(client, userdata, mid):
    print(f"📤 消息已发布，mid={mid}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

print("开始发布传感器数据...\n")

while True:
    for pet in pet_list:
        data = pet.read_all()
        for sensor_name, value in data.items():
            topic = f"{PUB_TOPIC_PREFIX}{pet.pet_id}/sensor/{sensor_name}"
            client.publish(topic, str(value))
    time.sleep(2)