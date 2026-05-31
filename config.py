# MQTT Broker 设置
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# 主题格式（使用 {pet_id} 占位符，实际订阅/发布时替换）
TOPIC_TEMP = "pet/{pet_id}/sensor/temp"
TOPIC_HUMI = "pet/{pet_id}/sensor/humi"
TOPIC_CAMERA = "pet/{pet_id}/camera/alert"
TOPIC_FEEDER = "pet/{pet_id}/control/feeder"
TOPIC_AC = "pet/{pet_id}/control/ac"
TOPIC_FEEDER_STATUS = "pet/{pet_id}/status/feeder"
TOPIC_AC_STATUS = "pet/{pet_id}/status/ac"
TOPIC_CAMERA_REQUEST = "pet/{pet_id}/camera/request"

# 默认阈值（当宠物未配置时使用）
DEFAULT_TEMP_MAX = 30.0
DEFAULT_HUMI_MIN = 40.0

# 数据库
DB_FILE = "pet_monitor.db"

# Web 端口
WEB_PORT = 5000