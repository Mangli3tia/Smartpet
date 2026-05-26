import eventlet
eventlet.monkey_patch()   # 必须放在最前面

import time
import threading
import sqlite3
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from config import (MQTT_BROKER, MQTT_PORT,
                    TOPIC_FEEDER, TOPIC_AC,
                    TOPIC_FEEDER_STATUS, TOPIC_AC_STATUS,
                    TOPIC_CAMERA_REQUEST,
                    DB_FILE, WEB_PORT)
from database import init_db, get_recent_sensor_data, get_recent_alerts, get_last_sensor_id, get_last_alert_id

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

last_sensor_id = 0
last_alert_id = 0

# MQTT 控制发布客户端
command_client = mqtt.Client()
command_client.connect(MQTT_BROKER, MQTT_PORT, 60)
command_client.loop_start()

# MQTT 状态反馈订阅客户端
status_client = mqtt.Client()
def on_status_connect(client, userdata, flags, rc):
    print("状态反馈客户端已连接")
    client.subscribe([(TOPIC_FEEDER_STATUS, 0), (TOPIC_AC_STATUS, 0)])
def on_status_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if topic == TOPIC_FEEDER_STATUS:
        socketio.emit('feeder_status', {'status': payload})
    elif topic == TOPIC_AC_STATUS:
        socketio.emit('ac_status', {'status': payload})
status_client.on_connect = on_status_connect
status_client.on_message = on_status_message
status_client.connect(MQTT_BROKER, MQTT_PORT, 60)
status_client.loop_start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@socketio.on('get_initial_data')
def handle_initial_data():
    sensor_data = get_recent_sensor_data(100)
    alerts = get_recent_alerts(20)
    timestamps = [row[0] for row in sensor_data]
    temps = [row[1] for row in sensor_data]
    humis = [row[2] for row in sensor_data]
    emit('initial_data', {
        'timestamps': timestamps,
        'temps': temps,
        'humis': humis,
        'alerts': alerts
    })

@socketio.on('camera_refresh')
def handle_camera_refresh(data):
    command_client.publish(TOPIC_CAMERA_REQUEST, "snapshot")
    emit('camera_refresh_result', {'status': 'request_sent'})

@socketio.on('control')
def handle_control(data):
    device = data.get('device')
    action = data.get('action')
    if device == 'feeder':
        command_client.publish(TOPIC_FEEDER, action)
        emit('control_result', {'device': 'feeder', 'status': '指令已发送'})
    elif device == 'ac':
        command_client.publish(TOPIC_AC, action)
        emit('control_result', {'device': 'ac', 'status': '指令已发送'})

def background_worker():
    global last_sensor_id, last_alert_id
    print("后台轮询线程已启动")
    with app.app_context():
        while True:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            # 新传感器数据
            c.execute("SELECT id, timestamp, temp, humi FROM sensor_data WHERE id > ? ORDER BY id", (last_sensor_id,))
            new_sensors = c.fetchall()
            for row in new_sensors:
                sid, ts, temp, humi = row
                socketio.emit('new_sensor', {'temp': temp, 'humi': humi, 'time': ts})
                last_sensor_id = sid
            # 新警报
            c.execute("SELECT id, timestamp, type, message, image_path FROM alerts WHERE id > ? ORDER BY id", (last_alert_id,))
            new_alerts = c.fetchall()
            for row in new_alerts:
                aid, ts, atype, msg, img = row
                socketio.emit('new_alert', {
                    'time': ts,
                    'type': atype,
                    'message': msg,
                    'image': img or ''
                })
                last_alert_id = aid
            conn.close()
            time.sleep(2)

if __name__ == '__main__':
    init_db()
    last_sensor_id = get_last_sensor_id()
    last_alert_id = get_last_alert_id()
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=True, allow_unsafe_werkzeug=True)