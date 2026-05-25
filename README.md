# 🐾 智能宠物监督系统

基于 MQTT 的物联网监控系统，模拟温湿度传感器和摄像头告警，通过规则引擎自动判断环境异常，并提供实时 Web 仪表盘展示数据。

## 📁 项目结构

petmonitor/
├── config.py              # 配置文件（MQTT地址、阈值等）
├── database.py            # 数据库操作（SQLite）
├── sensor_publisher.py    # 模拟温湿度传感器（发布端）
├── camera_publisher.py    # 模拟摄像头告警（发布端）
├── subscriber.py          # MQTT订阅端 + 规则引擎
├── web_server.py          # Web服务器 + SocketIO实时推送
├── templates/
│   └── dashboard.html     # 前端仪表盘页面
└── README.md

## 🔧 各模块功能

| 文件 | 功能 |
|------|------|
| config.py | 集中管理 MQTT Broker 地址、端口、主题名称、温度/湿度阈值、数据库文件等配置。 |
| database.py | 初始化 SQLite 数据库，提供保存传感器数据、保存报警记录、查询数据接口。 |
| sensor_publisher.py | 每2秒生成随机温湿度（温度15-35℃，湿度30-80%），通过 MQTT 发布。 |
| camera_publisher.py | 每10秒有30%概率模拟“宠物移动”事件，生成模拟图片名并发布告警。 |
| subscriber.py | 订阅 MQTT 主题，接收数据；执行规则引擎（温度>30℃或湿度<40%时报警）；将数据存入数据库。 |
| web_server.py | 启动 Flask Web 服务，通过 SocketIO 实时推送数据到前端页面。 |
| dashboard.html | 前端页面：使用 ECharts 显示温湿度历史曲线，实时更新当前值，展示警报列表。 |

## 🚀 快速开始

### 1. 安装依赖

在终端（确保已激活你的 Conda 环境）执行：

pip install paho-mqtt flask flask-socketio eventlet

> 推荐使用 paho-mqtt==1.6.1 以避免版本兼容问题。

### 2. 运行系统

需要同时运行四个终端（每个终端都先 cd 到项目目录 petmonitor）：

| 终端 | 命令 | 作用 |
|------|------|------|
| 1 | python subscriber.py | 启动订阅端（接收数据、规则引擎、存数据库） |
| 2 | python web_server.py | 启动 Web 服务器（访问 http://127.0.0.1:5000） |
| 3 | python sensor_publisher.py | 启动温湿度模拟器 |
| 4 | python camera_publisher.py | 启动摄像头模拟器 |

### 3. 打开浏览器

访问 http://127.0.0.1:5000，即可看到实时温湿度图表和警报信息。

## ⚙️ 规则引擎

- 高温警报：温度 > 30℃ 时触发。
- 低湿警报：湿度 < 40% 时触发。
- 摄像头告警：接收到摄像头主题消息时直接触发。

所有警报会存入数据库，并实时显示在网页上。

## 📦 自动生成的文件

- pet_monitor.db：SQLite 数据库（存储传感器数据和警报记录）。
- __pycache__/：Python 缓存目录（可安全删除）。

## ❓ 常见问题

Q: 网页一直显示“加载中...”？
A: 检查浏览器控制台（F12）是否有 WebSocket 连接错误；确认 web_server.py 中包含 @socketio.on('get_initial_data') 事件处理；重启 web_server.py 后刷新页面。

Q: 提示 ModuleNotFoundError: No module named 'paho'？
A: 未安装 paho-mqtt，执行 pip install paho-mqtt。

Q: paho-mqtt 版本报错 AttributeError: ...CallbackAPIVersion？
A: 你的版本可能太新，请降级到 1.6.1：pip install paho-mqtt==1.6.1。

Q: 摄像头模拟的图片不显示？
A: 模拟器只生成图片文件名，并未保存真实图片。你可以在项目目录下创建 static/ 文件夹，并放入同名占位图片（如 snapshot_xxx.jpg）即可显示。
