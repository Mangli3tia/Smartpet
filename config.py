import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "pet_monitor.db")

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# 默认宠物（Demo）主题（带 pet_id 占位符，每个 Demo 宠物独立数据流）
TOPIC_TEMP_DEFAULT = "demo/{pet_id}/sensor/temp"
TOPIC_HUMI_DEFAULT = "demo/{pet_id}/sensor/humi"
TOPIC_CAMERA_DEFAULT = "demo/{pet_id}/camera/alert"

# 自定义宠物（Own Pet）主题（带 pet_id 占位符）
TOPIC_TEMP_CUSTOM = "custom/{pet_id}/sensor/temp"
TOPIC_HUMI_CUSTOM = "custom/{pet_id}/sensor/humi"
TOPIC_CAMERA_CUSTOM = "custom/{pet_id}/camera/alert"

# 控制指令主题（带 pet_id）
TOPIC_FEEDER = "pet/{pet_id}/control/feeder"
TOPIC_AC = "pet/{pet_id}/control/ac"
TOPIC_FEEDER_STATUS = "pet/{pet_id}/status/feeder"
TOPIC_AC_STATUS = "pet/{pet_id}/status/ac"
TOPIC_CAMERA_REQUEST = "pet/{pet_id}/camera/request"

TOPIC_SYSTEM_PET_CREATED = "system/pet/created"

DEFAULT_TEMP_MAX = 30.0
DEFAULT_HUMI_MIN = 40.0
# 添加缺失的两个默认值
DEFAULT_CAMERA_SIMILARITY = 0.95
DEFAULT_CAMERA_INACTIVE = 5

DB_FILE = "pet_monitor.db"
WEB_PORT = 5000