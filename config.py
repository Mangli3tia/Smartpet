# MQTT Broker 设置（免费公共 Broker）
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# 传感器主题
TOPIC_TEMP = "pet/sensor/temp"
TOPIC_HUMI = "pet/sensor/humi"
TOPIC_CAMERA = "pet/camera/alert"

# 控制主题
TOPIC_FEEDER = "pet/control/feeder"
TOPIC_AC = "pet/control/ac"

# 状态反馈主题
TOPIC_FEEDER_STATUS = "pet/status/feeder"
TOPIC_AC_STATUS = "pet/status/ac"
TOPIC_CAMERA_REQUEST = "pet/camera/request"   # 手动拍照请求

# 规则引擎阈值
TEMP_MAX = 30.0   # 温度超过此值触发高温警报
HUMI_MIN = 40.0   # 湿度低于此值触发低湿警报

# 数据库文件
DB_FILE = "pet_monitor.db"

# Web 服务端口
WEB_PORT = 5000