import board
import adafruit_dht
import time
import json

SENSOR_PIN_MAP = {1: board.D4}

def generate_sensor_data(device_id=1):
    pin = SENSOR_PIN_MAP.get(device_id, board.D4)
    for attempt in range(3):
        dht = adafruit_dht.DHT22(pin, use_pulseio=False)
        try:
            temperature = dht.temperature
            humidity = dht.humidity
            if temperature is not None and humidity is not None:
                return round(temperature, 1), round(humidity, 1)
        except RuntimeError as e:
            pass
        finally:
            dht.exit()
        time.sleep(0.3)
    print(f"DHT22 read failed after 3 attempts — skipping")
    return None, None

def format_temp_payload(temp):
    return json.dumps({"value": temp})

def format_humi_payload(humi):
    return json.dumps({"value": humi})