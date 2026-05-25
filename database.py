import sqlite3
from config import DB_FILE
from datetime import datetime

def init_db():
    """初始化数据库表（如果不存在）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  temp REAL,
                  humi REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  type TEXT,
                  message TEXT,
                  image_path TEXT)''')
    conn.commit()
    conn.close()

def save_sensor_data(temp, humi):
    """保存一条温湿度记录"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (timestamp, temp, humi) VALUES (?,?,?)",
              (datetime.now().isoformat(), temp, humi))
    conn.commit()
    conn.close()

def save_alert(alert_type, message, image_path=""):
    """保存一条警报记录"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO alerts (timestamp, type, message, image_path) VALUES (?,?,?,?)",
              (datetime.now().isoformat(), alert_type, message, image_path))
    conn.commit()
    conn.close()

def get_recent_sensor_data(limit=100):
    """获取最近的 sensor_data 记录（按时间正序）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, temp, humi FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))   # 变为正序

def get_recent_alerts(limit=20):
    """获取最近的警报记录（倒序，最新的在前）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, type, message, image_path FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_last_sensor_id():
    """获取最新的 sensor_data 的 id（用于轮询增量更新）"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM sensor_data")
    row = c.fetchone()
    conn.close()
    return row[0] if row[0] else 0

def get_last_alert_id():
    """获取最新的 alert 的 id"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM alerts")
    row = c.fetchone()
    conn.close()
    return row[0] if row[0] else 0