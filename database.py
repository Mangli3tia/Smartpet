import sqlite3
from config import DB_FILE, DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN
from datetime import datetime

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  pet_id INTEGER,
                  timestamp TEXT,
                  temp REAL,
                  humi REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  pet_id INTEGER,
                  timestamp TEXT,
                  type TEXT,
                  message TEXT,
                  image_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  species TEXT,
                  age INTEGER,
                  photo TEXT,
                  temp_max REAL,
                  humi_min REAL,
                  created_at TEXT,
                  type TEXT DEFAULT 'default',
                  temp_sensor_id INTEGER,
                  camera_id INTEGER)''')
    # 插入默认宠物（如果为空）
    c.execute("SELECT COUNT(*) FROM pets WHERE type='default'")
    if c.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO pets (name, species, temp_max, humi_min, created_at, type) VALUES (?,?,?,?,?,?)",
                  ("Fluffy", "DemoCat", DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN, now, "default"))
        c.execute("INSERT INTO pets (name, species, temp_max, humi_min, created_at, type) VALUES (?,?,?,?,?,?)",
                  ("Buddy", "DemoDog", DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN, now, "default"))
    conn.commit()
    conn.close()

def get_pets():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, species, age, photo, temp_max, humi_min, type FROM pets")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "species": r[2], "age": r[3], "photo": r[4],
             "temp_max": r[5], "humi_min": r[6], "type": r[7]} for r in rows]

def get_default_pets():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM pets WHERE type='default'")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

def get_custom_pets():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM pets WHERE type='custom'")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

def get_pet_thresholds(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT temp_max, humi_min FROM pets WHERE id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"temp_max": row[0], "humi_min": row[1]}
    return {"temp_max": DEFAULT_TEMP_MAX, "humi_min": DEFAULT_HUMI_MIN}

def create_pet(name, species, temp_max, humi_min, temp_sensor_id=None, camera_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""INSERT INTO pets (name, species, temp_max, humi_min, created_at, type, temp_sensor_id, camera_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (name, species, temp_max, humi_min, now, "custom", temp_sensor_id, camera_id))
    pet_id = c.lastrowid
    conn.commit()
    conn.close()
    return pet_id

def update_pet_thresholds(pet_id, temp_max=None, humi_min=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if temp_max is not None:
        c.execute("UPDATE pets SET temp_max = ? WHERE id = ?", (temp_max, pet_id))
    if humi_min is not None:
        c.execute("UPDATE pets SET humi_min = ? WHERE id = ?", (humi_min, pet_id))
    conn.commit()
    conn.close()

def get_devices():
    return [
        {"id": 1, "name": "DHT22 Sensor #1", "type": "temp_humi"},
        {"id": 2, "name": "USB Camera #1", "type": "camera"}
    ]

def save_sensor_data(pet_id, temp, humi):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (pet_id, timestamp, temp, humi) VALUES (?,?,?,?)",
              (pet_id, datetime.now().isoformat(), temp, humi))
    conn.commit()
    conn.close()

def save_alert(pet_id, alert_type, message, image_path=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO alerts (pet_id, timestamp, type, message, image_path) VALUES (?,?,?,?,?)",
              (pet_id, datetime.now().isoformat(), alert_type, message, image_path))
    conn.commit()
    conn.close()

def get_recent_sensor_data(pet_id, limit=100):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, temp, humi FROM sensor_data WHERE pet_id=? ORDER BY id DESC LIMIT ?",
              (pet_id, limit))
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))

def get_recent_alerts(pet_id, limit=20):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, type, message, image_path FROM alerts WHERE pet_id=? ORDER BY id DESC LIMIT ?",
              (pet_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_last_sensor_id(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM sensor_data WHERE pet_id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row[0] else 0

def get_last_alert_id(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM alerts WHERE pet_id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row[0] else 0