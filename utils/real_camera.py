import cv2
import time
import os

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

def capture_image(device_id=2, event_type="manual"):
    # 设备ID到摄像头索引的映射（根据实际情况修改）
    index_map = {2: 0}
    index = index_map.get(device_id, 0)
    for attempt in range(3):
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"Camera open failed (attempt {attempt+1}), index={index}")
            time.sleep(0.5)
            continue
        ret, frame = cap.read()
        cap.release()
        if ret:
            timestamp = int(time.time())
            img_name = f"real_{timestamp}.jpg"
            img_path = os.path.join(STATIC_DIR, img_name)
            cv2.imwrite(img_path, frame)
            print(f"Real snapshot saved: {img_path}")
            return img_name
        else:
            print(f"Frame read failed (attempt {attempt+1})")
        time.sleep(0.5)
    print("Camera capture failed after 3 attempts")
    return None

def create_alert_message(event_type, img_name):
    return {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "image": img_name
    }