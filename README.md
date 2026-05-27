# 🐾 智能宠物监督系统

基于 MQTT 的物联网宠物监控平台，模拟温湿度传感器和摄像头，具备规则引擎、远程控制（喂食器、空调）和实时 Web 仪表盘。

## ✨ 功能特性

- **环境实时监测**：模拟温度（15–35℃）和湿度（30–80%），每2秒更新一次。
- **智能摄像头**：
  - 自动随机抓拍（每10秒30%概率），生成真实图片（随机背景色 + 时间文字）。
  - 手动抓拍：点击网页按钮，10秒倒计时后生成新图片并自动显示。
- **规则引擎**：
  - 高温警报（>30℃）和低湿警报（<40%），存入数据库并在前端展示。
  - 摄像头告警（宠物移动）附带图片预览。
- **远程控制**：
  - 通过网页按钮控制喂食器和空调开关。
  - 模拟执行并反馈状态（“喂食成功”、“空调已开启/关闭”）。
- **实时仪表盘**：
  - 温湿度仪表盘及历史趋势图（ECharts）。
  - 最新抓拍图片展示。
  - 警报列表（含时间戳和缩略图）。
  - 所有数据通过 WebSocket 自动推送，无需手动刷新页面。

## 📁 项目结构

SmartPet/
├── config.py # MQTT 配置（服务器地址、主题、阈值等）
├── database.py # SQLite 数据库操作
├── publisher.py # 统一发布端（温湿度 + 摄像头）
├── subscriber.py # 订阅端（规则引擎、数据库、执行器调用）
├── web_server.py # Flask Web 服务 + SocketIO + MQTT 指令发布
├── templates/
│ └── dashboard.html # 前端界面（英文）
├── utils/
│ ├── init.py
│ ├── sensor_emulator.py # 温湿度数据模拟
│ ├── camera_emulator.py # 真实图片生成（Pillow）
│ ├── feeder.py # 喂食器控制逻辑（模拟）
│ └── ac.py # 空调控制逻辑（模拟）
├── static/ # 自动创建，存放抓拍图片
└── README.md

1. 安装依赖

在终端中（确保已激活你的 Conda 环境，例如 `MQTT`）执行：

```bash
pip install paho-mqtt flask flask-socketio eventlet pillow

2. 运行系统
打开三个终端，都切换到项目根目录 SmartPet/，分别运行：

终端	命令	说明
1	python subscriber.py	订阅端：规则引擎、数据库、执行器控制
2	python web_server.py	Web 服务器 + SocketIO + MQTT 指令分发
3	python publisher.py	统一发布端（传感器 + 摄像头模拟）

3. 访问网页
打开浏览器，访问 http://127.0.0.1:5000 或 http://localhost:5000。

你将看到：

当前温度、湿度（自动更新）

历史趋势曲线（ECharts）

最新抓拍图片（自动或手动）

远程控制按钮（喂食器、空调）

警报列表（环境警报 + 摄像头告警）

## 🖱️ 前端操作指南
手动抓拍：点击“Refresh Camera”按钮 → 10秒倒计时 → 新图片自动显示。

喂食器：点击“Feeder”按钮 → 状态显示“Feed success”（模拟）。

空调：点击“AC On”/“AC Off” → 状态显示“AC turned on/off”。

警报：当温度>30℃、湿度<40%或收到摄像头告警时，自动出现在警报列表中。

最新图片：任何摄像头告警（自动或手动）都会更新图片区域。

## 🔧 扩展为真实硬件
所有模拟代码都集中在 utils/ 目录下，便于替换：

替换 utils/sensor_emulator.py → 读取真实温湿度传感器（如 DHT11，使用 Adafruit_DHT）。

替换 utils/camera_emulator.py → 使用 OpenCV 调用真实摄像头拍照并保存到 static/。

替换 utils/feeder.py 和 utils/ac.py → 控制 GPIO、继电器或红外发射（例如树莓派）。

替换后，其他模块（subscriber.py、web_server.py、dashboard.html）无需修改。