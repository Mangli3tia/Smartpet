import random
import json

def generate_sensor_data():
    temp = round(random.uniform(15, 35), 1)
    humi = random.randint(30, 80)
    return temp, humi

def format_temp_payload(temp):
    return json.dumps({"value": temp})

def format_humi_payload(humi):
    return json.dumps({"value": humi})