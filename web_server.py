import eventlet
eventlet.monkey_patch()

import time
import threading
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS,
                    TOPIC_CAMERA_REQUEST,
                    DB_FILE, WEB_PORT)
from database import (init_db, get_pets, get_recent_sensor_data, get_recent_alerts,
                      get_last_sensor_id, get_last_alert_id, get_pet_thresholds)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储每个宠物上次推送的 ID
last_sensor_id = {}
last_alert_id = {}

# MQTT 客户端用于发布控制指令
command_client = mqtt.Client()
command_client.connect(MQTT_BROKER, MQTT_PORT, 60)
command_client.loop_start()

# MQTT 客户端用于订阅状态反馈
status_client = mqtt.Client()
def on_status_connect(client, userdata, flags, rc):
    client.subscribe("pet/+/status/feeder")
    client.subscribe("pet/+/status/ac")
def on_status_message(client, userdata, msg):
    parts = msg.topic.split('/')
    if len(parts) >= 4:
        try:
            pet_id = int(parts[1])
        except:
            return
        status = msg.payload.decode()
        if parts[3] == 'feeder':
            socketio.emit('feeder_status', {'pet_id': pet_id, 'status': status})
        elif parts[3] == 'ac':
            socketio.emit('ac_status', {'pet_id': pet_id, 'status': status})
status_client.on_connect = on_status_connect
status_client.on_message = on_status_message
status_client.connect(MQTT_BROKER, MQTT_PORT, 60)
status_client.loop_start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/pets')
def api_pets():
    return jsonify(get_pets())

@app.route('/api/history/<int:pet_id>')
def api_history(pet_id):
    limit = request.args.get('limit', 100, type=int)
    data = get_recent_sensor_data(pet_id, limit)
    timestamps = [row[0] for row in data]
    temps = [row[1] for row in data]
    humis = [row[2] for row in data]
    return jsonify({'timestamps': timestamps, 'temps': temps, 'humis': humis})

@app.route('/api/alerts/<int:pet_id>')
def api_alerts(pet_id):
    limit = request.args.get('limit', 20, type=int)
    rows = get_recent_alerts(pet_id, limit)
    return jsonify([{'time': r[0], 'type': r[1], 'message': r[2], 'image': r[3]} for r in rows])

@socketio.on('get_initial_data')
def handle_initial_data(data):
    pet_id = data.get('pet_id')
    if pet_id is None:
        return
    sensor_data = get_recent_sensor_data(pet_id, 100)
    alerts = get_recent_alerts(pet_id, 20)
    timestamps = [row[0] for row in sensor_data]
    temps = [row[1] for row in sensor_data]
    humis = [row[2] for row in sensor_data]
    emit('initial_data', {
        'pet_id': pet_id,
        'timestamps': timestamps,
        'temps': temps,
        'humis': humis,
        'alerts': alerts
    })

@socketio.on('camera_refresh')
def handle_camera_refresh(data):
    pet_id = data.get('pet_id')
    if pet_id is None:
        return
    topic = TOPIC_CAMERA_REQUEST.format(pet_id=pet_id)
    command_client.publish(topic, "snapshot")
    emit('camera_refresh_result', {'pet_id': pet_id, 'status': 'request_sent'})

@socketio.on('control')
def handle_control(data):
    pet_id = data.get('pet_id')
    device = data.get('device')
    action = data.get('action')
    if pet_id is None or device is None or action is None:
        return
    if device == 'feeder':
        topic = TOPIC_FEEDER.format(pet_id=pet_id)
        command_client.publish(topic, action)
        emit('control_result', {'pet_id': pet_id, 'device': 'feeder', 'status': 'Command sent'})
    elif device == 'ac':
        topic = TOPIC_AC.format(pet_id=pet_id)
        command_client.publish(topic, action)
        emit('control_result', {'pet_id': pet_id, 'device': 'ac', 'status': 'Command sent'})

def background_worker():
    """轮询所有宠物的新数据并推送到前端"""
    with app.app_context():
        while True:
            pets = get_pets()
            for pet in pets:
                pid = pet['id']
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                # 传感器数据
                last_id = last_sensor_id.get(pid, 0)
                c.execute("SELECT id, timestamp, temp, humi FROM sensor_data WHERE pet_id=? AND id>? ORDER BY id", (pid, last_id))
                new_sensors = c.fetchall()
                for row in new_sensors:
                    sid, ts, temp, humi = row
                    socketio.emit('new_sensor', {'pet_id': pid, 'temp': temp, 'humi': humi, 'time': ts})
                    last_sensor_id[pid] = sid
                # 警报
                last_id = last_alert_id.get(pid, 0)
                c.execute("SELECT id, timestamp, type, message, image_path FROM alerts WHERE pet_id=? AND id>? ORDER BY id", (pid, last_id))
                new_alerts = c.fetchall()
                for row in new_alerts:
                    aid, ts, atype, msg, img = row
                    socketio.emit('new_alert', {
                        'pet_id': pid,
                        'time': ts,
                        'type': atype,
                        'message': msg,
                        'image': img or ''
                    })
                    last_alert_id[pid] = aid
                conn.close()
            time.sleep(2)

if __name__ == '__main__':
    init_db()
    pets = get_pets()
    for pet in pets:
        last_sensor_id[pet['id']] = get_last_sensor_id(pet['id'])
        last_alert_id[pet['id']] = get_last_alert_id(pet['id'])
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=True, allow_unsafe_werkzeug=True)