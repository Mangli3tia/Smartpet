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
                      get_last_sensor_id, get_last_alert_id, get_pet_thresholds,
                      create_pet, update_pet_thresholds, get_devices)

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

# ---------- 数据库迁移 ----------
def migrate_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(pets)")
    columns = [col[1] for col in c.fetchall()]
    if 'type' not in columns:
        c.execute("ALTER TABLE pets ADD COLUMN type TEXT DEFAULT 'default'")
    if 'temp_sensor_id' not in columns:
        c.execute("ALTER TABLE pets ADD COLUMN temp_sensor_id INTEGER")
    if 'camera_id' not in columns:
        c.execute("ALTER TABLE pets ADD COLUMN camera_id INTEGER")
    conn.commit()
    conn.close()

# ---------- 页面路由 ----------
@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/create-pet')
def create_pet_page():
    return render_template('create_pet.html')

@app.route('/manage-pets')
def manage_pets():
    return render_template('manage_pets.html')

# ---------- API 路由 ----------
@app.route('/api/devices')
def api_devices():
    return jsonify(get_devices())

@app.route('/api/pets')
def api_pets():
    return jsonify(get_pets())

@app.route('/api/pets', methods=['POST'])
def api_create_pet():
    data = request.json
    name = data.get('name')
    species = data.get('species', 'Custom')
    temp_sensor_id = data.get('temp_sensor_id')
    camera_id = data.get('camera_id')
    temp_max = data.get('temp_max', 30.0)
    humi_min = data.get('humi_min', 40.0)
    if not name:
        return jsonify({"error": "Pet name required"}), 400
    pet_id = create_pet(name, species, temp_max, humi_min, temp_sensor_id, camera_id)
    return jsonify({"pet_id": pet_id, "message": "Pet created"}), 201

@app.route('/api/pets/<int:pet_id>', methods=['PUT'])
def api_update_pet(pet_id):
    data = request.json
    name = data.get('name')
    species = data.get('species')
    temp_max = data.get('temp_max')
    humi_min = data.get('humi_min')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if name:
        c.execute("UPDATE pets SET name = ? WHERE id = ?", (name, pet_id))
    if species:
        c.execute("UPDATE pets SET species = ? WHERE id = ?", (species, pet_id))
    if temp_max is not None:
        c.execute("UPDATE pets SET temp_max = ? WHERE id = ?", (temp_max, pet_id))
    if humi_min is not None:
        c.execute("UPDATE pets SET humi_min = ? WHERE id = ?", (humi_min, pet_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Pet updated"})

@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
def api_delete_pet(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT type FROM pets WHERE id=?", (pet_id,))
    row = c.fetchone()
    if not row:
        return jsonify({"error": "Pet not found"}), 404
    if row[0] == 'default':
        return jsonify({"error": "Cannot delete demo pet"}), 403
    c.execute("DELETE FROM pets WHERE id=?", (pet_id,))
    c.execute("DELETE FROM sensor_data WHERE pet_id=?", (pet_id,))
    c.execute("DELETE FROM alerts WHERE pet_id=?", (pet_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Pet deleted"})

@app.route('/api/pets/<int:pet_id>/thresholds', methods=['PUT'])
def api_update_thresholds(pet_id):
    data = request.json
    temp_max = data.get('temp_max')
    humi_min = data.get('humi_min')
    if temp_max is None and humi_min is None:
        return jsonify({"error": "No threshold provided"}), 400
    update_pet_thresholds(pet_id, temp_max, humi_min)
    return jsonify({"message": "Thresholds updated"})

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

# ---------- SocketIO 事件 ----------
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

# ---------- 后台轮询 ----------
def background_worker():
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
    migrate_database()
    pets = get_pets()
    for pet in pets:
        last_sensor_id[pet['id']] = get_last_sensor_id(pet['id'])
        last_alert_id[pet['id']] = get_last_alert_id(pet['id'])
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=True, allow_unsafe_werkzeug=True)