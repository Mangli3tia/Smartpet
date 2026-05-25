import time
import threading
import sqlite3
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from config import DB_FILE, WEB_PORT
from database import init_db, get_recent_sensor_data, get_recent_alerts, get_last_sensor_id, get_last_alert_id

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 记录上次推送的数据库ID
last_sensor_id = 0
last_alert_id = 0

@app.route('/')
def index():
    return render_template('dashboard.html')

@socketio.on('get_initial_data')
def handle_initial_data():
    """客户端连接时发送历史数据和最新警报"""
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

def background_worker():
    """后台线程：轮询数据库，有新数据就通过 WebSocket 推送给前端"""
    global last_sensor_id, last_alert_id
    with app.app_context():
        while True:
            # 检查新的传感器数据
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, timestamp, temp, humi FROM sensor_data WHERE id > ? ORDER BY id", (last_sensor_id,))
            new_sensors = c.fetchall()
            for row in new_sensors:
                sensor_id, ts, temp, humi = row
                socketio.emit('new_sensor', {'temp': temp, 'humi': humi, 'time': ts})
                last_sensor_id = sensor_id

            # 检查新的警报
            c.execute("SELECT id, timestamp, type, message, image_path FROM alerts WHERE id > ? ORDER BY id", (last_alert_id,))
            new_alerts = c.fetchall()
            for row in new_alerts:
                alert_id, ts, atype, msg, img = row
                socketio.emit('new_alert', {
                    'time': ts,
                    'type': atype,
                    'message': msg,
                    'image': img or ''
                })
                last_alert_id = alert_id
            conn.close()
            time.sleep(2)   # 每2秒轮询一次

if __name__ == '__main__':
    init_db()
    # 初始化 last_id
    last_sensor_id = get_last_sensor_id()
    last_alert_id = get_last_alert_id()
    # 启动后台轮询线程
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=True, allow_unsafe_werkzeug=True)