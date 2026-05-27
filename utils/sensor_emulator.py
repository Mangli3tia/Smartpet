import random
import json

def generate_sensor_data():
    """生成随机温湿度数据，返回 (温度, 湿度)"""
    temp = round(random.uniform(15, 35), 1)
    humi = random.randint(30, 80)
    return temp, humi

def format_temp_payload(temp):
    return json.dumps({"value": temp})

def format_humi_payload(humi):
    return json.dumps({"value": humi})