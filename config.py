# MQTT Broker 设置（免费公共 Broker）
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# 主题定义
TOPIC_TEMP = "pet/sensor/temp"
TOPIC_HUMI = "pet/sensor/humi"
TOPIC_CAMERA = "pet/camera/alert"

# 规则引擎阈值
TEMP_MAX = 30.0   # 温度超过此值触发高温警报
HUMI_MIN = 40.0   # 湿度低于此值触发低湿警报

# 数据库文件
DB_FILE = "pet_monitor.db"

# Web 服务端口
WEB_PORT = 5000