import sqlite3
import time
from config.settings import DB_PATH

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id TEXT,
            time TEXT,
            sensor_type TEXT,
            value REAL
        )
    ''')
    conn.commit()
    conn.close()

# 存数据：参数全部由订阅端传进来！
def save_data(pet_id, sensor_type, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO pet_records (pet_id, time, sensor_type, value)
        VALUES (?, ?, ?, ?)
    ''', (pet_id, now, sensor_type, float(value)))
    conn.commit()
    conn.close()

init_db()