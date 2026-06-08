import sqlite3
from config import DB_FILE, DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN, DEFAULT_CAMERA_SIMILARITY, DEFAULT_CAMERA_INACTIVE
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
                  camera_id INTEGER,
                  camera_similarity REAL DEFAULT 0.95,
                  camera_inactive INTEGER DEFAULT 5,
                  camera_alert_probability REAL DEFAULT 0.3)''')
    # 插入默认宠物（type='default'）
    c.execute("SELECT COUNT(*) FROM pets WHERE type='default'")
    if c.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO pets (name, species, temp_max, humi_min, created_at, type) VALUES (?,?,?,?,?,?)",
                  ("Fluffy", "Cat", DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN, now, "default"))
        c.execute("INSERT INTO pets (name, species, temp_max, humi_min, created_at, type) VALUES (?,?,?,?,?,?)",
                  ("Buddy", "Dog", DEFAULT_TEMP_MAX, DEFAULT_HUMI_MIN, now, "default"))
    conn.commit()
    conn.close()

def get_pets_by_type(pet_type):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, species, age, photo, temp_max, humi_min, type FROM pets WHERE type=?", (pet_type,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "species": r[2], "age": r[3], "photo": r[4],
             "temp_max": r[5], "humi_min": r[6], "type": r[7]} for r in rows]

def get_all_pets():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, species, age, photo, temp_max, humi_min, type, temp_sensor_id, camera_id, camera_similarity, camera_inactive, camera_alert_probability FROM pets")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "species": r[2], "age": r[3], "photo": r[4],
             "temp_max": r[5], "humi_min": r[6], "type": r[7],
             "temp_sensor_id": r[8], "camera_id": r[9],
             "camera_similarity": r[10], "camera_inactive": r[11],
             "camera_alert_probability": r[12] if r[12] is not None else 0.3} for r in rows]

def get_pet_thresholds(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT temp_max, humi_min, camera_alert_probability FROM pets WHERE id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"temp_max": row[0], "humi_min": row[1], "camera_alert_probability": row[2] if row[2] is not None else 0.3}
    return {"temp_max": DEFAULT_TEMP_MAX, "humi_min": DEFAULT_HUMI_MIN, "camera_alert_probability": 0.3}

def get_pet_camera_config(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT camera_similarity, camera_inactive FROM pets WHERE id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"similarity": row[0], "inactive": row[1]}
    return {"similarity": DEFAULT_CAMERA_SIMILARITY, "inactive": DEFAULT_CAMERA_INACTIVE}

def update_pet_camera_config(pet_id, similarity=None, inactive=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if similarity is not None:
        c.execute("UPDATE pets SET camera_similarity = ? WHERE id = ?", (similarity, pet_id))
    if inactive is not None:
        c.execute("UPDATE pets SET camera_inactive = ? WHERE id = ?", (inactive, pet_id))
    conn.commit()
    conn.close()

def get_pet_type(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT type FROM pets WHERE id=?", (pet_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 'default'

def create_pet(name, species, temp_max, humi_min, temp_sensor_id=None, camera_id=None,
               pet_type='custom', camera_similarity=None, camera_inactive=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().isoformat()
    if camera_similarity is None:
        camera_similarity = DEFAULT_CAMERA_SIMILARITY
    if camera_inactive is None:
        camera_inactive = DEFAULT_CAMERA_INACTIVE
    c.execute("""INSERT INTO pets (name, species, temp_max, humi_min, created_at, type, temp_sensor_id, camera_id, camera_similarity, camera_inactive)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (name, species, temp_max, humi_min, now, pet_type, temp_sensor_id, camera_id, camera_similarity, camera_inactive))
    pet_id = c.lastrowid
    conn.commit()
    conn.close()
    return pet_id

def update_pet_thresholds(pet_id, temp_max=None, humi_min=None, camera_alert_probability=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if temp_max is not None:
        c.execute("UPDATE pets SET temp_max = ? WHERE id = ?", (temp_max, pet_id))
    if humi_min is not None:
        c.execute("UPDATE pets SET humi_min = ? WHERE id = ?", (humi_min, pet_id))
    if camera_alert_probability is not None:
        c.execute("UPDATE pets SET camera_alert_probability = ? WHERE id = ?", (camera_alert_probability, pet_id))
    conn.commit()
    conn.close()

def update_pet(pet_id, name=None, species=None, temp_max=None, humi_min=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if name is not None:
        c.execute("UPDATE pets SET name = ? WHERE id = ?", (name, pet_id))
    if species is not None:
        c.execute("UPDATE pets SET species = ? WHERE id = ?", (species, pet_id))
    if temp_max is not None:
        c.execute("UPDATE pets SET temp_max = ? WHERE id = ?", (temp_max, pet_id))
    if humi_min is not None:
        c.execute("UPDATE pets SET humi_min = ? WHERE id = ?", (humi_min, pet_id))
    conn.commit()
    conn.close()

def delete_pet(pet_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sensor_data WHERE pet_id=?", (pet_id,))
    c.execute("DELETE FROM alerts WHERE pet_id=?", (pet_id,))
    c.execute("DELETE FROM pets WHERE id=?", (pet_id,))
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