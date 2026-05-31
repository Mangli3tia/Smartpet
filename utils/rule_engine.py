# utils/rule_engine.py
from database import get_pet_thresholds

def evaluate(pet_id, event_type, payload):
    """
    event_type: 'temp', 'humi', 'camera'
    payload: dict, 例如 {'value': 32.5} 或 {'time': '...', 'image': '...'}
    """
    alerts = []
    thresholds = get_pet_thresholds(pet_id)
    if event_type == 'temp':
        temp = payload.get('value', 0)
        if temp > thresholds['temp_max']:
            alerts.append(f"High temperature alert: {temp}°C exceeds threshold {thresholds['temp_max']}°C")
    elif event_type == 'humi':
        humi = payload.get('value', 100)
        if humi < thresholds['humi_min']:
            alerts.append(f"Low humidity alert: {humi}% below threshold {thresholds['humi_min']}%")
    elif event_type == 'camera':
        event_time = payload.get('time', '')
        alerts.append(f"Pet movement detected at {event_time}")
    return alerts