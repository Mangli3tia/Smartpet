import random
import cv2
import numpy as np
import os
from database import get_pet_thresholds, get_pet_type
from config import DEFAULT_CAMERA_SIMILARITY, DEFAULT_CAMERA_INACTIVE



_last_hist = {}
_inactive_counter = {}

def get_image_histogram(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist

def rule_high_temperature(pet_id, payload):
    if payload.get('type') != 'temp':
        return []
    thresholds = get_pet_thresholds(pet_id)
    temp = payload.get('value', 0)
    if temp > thresholds['temp_max']:
        return [f"High temperature alert: {temp}°C exceeds threshold {thresholds['temp_max']}°C"]
    return []

def rule_low_humidity(pet_id, payload):
    if payload.get('type') != 'humi':
        return []
    thresholds = get_pet_thresholds(pet_id)
    humi = payload.get('value', 100)
    if humi < thresholds['humi_min']:
        return [f"Low humidity alert: {humi}% below threshold {thresholds['humi_min']}%"]
    return []

def rule_camera_alert(pet_id, payload):
    if payload.get('type') != 'camera':
        return []
    img_path = payload.get('image', '')
    if not img_path:
        return []
    full_path = os.path.join("static", img_path)
    if not os.path.exists(full_path):
        return []

    pet_type = get_pet_type(pet_id)
    event_time = payload.get('time', '')

    if pet_type == 'default':
        # 模拟宠物：30% 概率告警
        if random.random() < 0.3:
            return [f"Simulated pet movement detected at {event_time}"]
        else:
            return []
    else:
        # 真实宠物：检测长时间静止
        current_hist = get_image_histogram(full_path)
        if current_hist is None:
            return []
        last_hist = _last_hist.get(pet_id)
        if last_hist is None:
            _last_hist[pet_id] = current_hist
            _inactive_counter[pet_id] = 0
            return []
        similarity = cv2.compareHist(last_hist, current_hist, cv2.HISTCMP_CORREL)
        _last_hist[pet_id] = current_hist

        if similarity > DEFAULT_CAMERA_SIMILARITY:
            _inactive_counter[pet_id] = _inactive_counter.get(pet_id, 0) + 1
        else:
            _inactive_counter[pet_id] = 0


        if _inactive_counter[pet_id] >= DEFAULT_CAMERA_INACTIVE:
            _inactive_counter[pet_id] = 0
            return [f"Alert: Pet has been inactive for a long time (no change in {DEFAULT_CAMERA_INACTIVE} consecutive snapshots) at {event_time}"]
        else:
            return []

RULES = [rule_high_temperature, rule_low_humidity, rule_camera_alert]

def evaluate(pet_id, event_type, payload):
    alerts = []
    payload['type'] = event_type
    for rule in RULES:
        result = rule(pet_id, payload)
        if result:
            alerts.extend(result)
    return alerts