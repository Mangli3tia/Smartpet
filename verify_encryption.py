"""验证 MQTT 加密：同时监听 broker 原始密文 vs 解密后明文"""
import paho.mqtt.client as mqtt
from config import ENCRYPTION_KEY, MQTT_BROKER, MQTT_PORT
from utils.crypto import decrypt

def on_msg(client, userdata, msg):
    raw = msg.payload.decode()
    try:
        plain = decrypt(raw, ENCRYPTION_KEY)
    except Exception:
        plain = "[解密失败]"

    print(f"TOPIC : {msg.topic}")
    print(f"CIPHER: {raw[:70]}...")
    print(f"PLAIN : {plain}")
    print("-" * 50)

client = mqtt.Client()
client.on_message = on_msg
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe("demo/+/sensor/temp")
client.subscribe("demo/+/sensor/humi")
print(f"Listening on broker.emqx.io for encrypted messages...\n")
client.loop_forever()
