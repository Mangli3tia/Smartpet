import board
import adafruit_dht
import time
import json
import random

SENSOR_PIN_MAP = {1: board.D4}

def generate_sensor_data(device_id=1):
    pin = SENSOR_PIN_MAP.get(device_id, board.D4)
    dht = adafruit_dht.DHT22(pin, use_pulseio=False)
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        if temperature is not None and humidity is not None:
            return round(temperature, 1), round(humidity, 1)
        else:
            print("DHT22 read None, using fallback")
            return round(random.uniform(15,35),1), random.randint(30,80)
    except RuntimeError as e:
        print(f"DHT22 error: {e}, using fallback")
        return round(random.uniform(15,35),1), random.randint(30,80)
    finally:
        dht.exit()

def format_temp_payload(temp):
    return json.dumps({"value": temp})

def format_humi_payload(humi):
    return json.dumps({"value": humi})