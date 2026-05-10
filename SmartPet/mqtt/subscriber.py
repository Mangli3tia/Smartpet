import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT, SUB_TOPIC
from utils.handler import handle_message
from utils.database import init_db

def on_connect(client, userdata, flags, rc):
    print("✅ 订阅端已连接 MQTT")
    client.subscribe(SUB_TOPIC)

def on_message(client, user, msg):
    handle_message(msg.topic, msg.payload)

if __name__ == "__main__":
    init_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()