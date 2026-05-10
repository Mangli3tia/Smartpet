from utils.database import save_data
from utils.rule_engine import check_and_run

def handle_message(topic, payload):
    try:
        # 从主题里直接拆出：宠物ID、传感器类型
        parts = topic.split("/")
        pet_id = parts[2]          # 小白/小黑/小花
        sensor_type = parts[4]     # temp/active/humidity
        value = payload.decode()   # 数值

        # 直接打印：谁的什么属性是多少
        print(f"宠物【{pet_id}】 | {sensor_type}: {value}")

        check_and_run(sensor_type, value, pet_id)

        save_data(pet_id, sensor_type, value)

    except Exception:
        pass