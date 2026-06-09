# 🐾 Smart Pet Monitoring System / 智能宠物监督系统

*An MQTT-based IoT pet monitoring platform with dual-mode support (simulated & real hardware), featuring sensor telemetry, camera analysis, rule engine, remote control, and a real-time web dashboard.*

基于 MQTT 的物联网宠物远程监控平台，支持 Demo 模拟与 Own Pet 真实硬件双模式，具备传感器采集、摄像头分析、规则引擎、远程控制和实时 Web 仪表盘。

---

## ✨ Features / 功能特性

### Dual Mode / 双模式运行

| Mode / 模式 | Data Source / 数据来源 | Environment / 适用环境 |
|-------------|------------------------|------------------------|
| **Demo Mode** | Simulated sensors + camera / 模拟传感器 + 模拟摄像头 | Windows / macOS / Linux，无需硬件 |
| **Own Pet Mode** | DHT22 + USB camera / DHT22 温湿度传感器 + USB 摄像头 | Raspberry Pi / 树莓派等嵌入式设备 |

- Demo 与 Own Pet **严格分离**，绝不混用数据源 — *Strict separation; data sources are never mixed*
- Demo 模式可创建任意数量的模拟宠物，各有独立的随机数据流 — *Create unlimited simulated pets with independent data streams*
- Own Pet 无硬件时静默跳过，不产生虚假数据 — *Silently skips when hardware is unavailable; no fake data*

### Environment Monitoring / 环境监测
- 温湿度每 2 秒采集，实时推送 — *Temp & humidity sampled every 2 seconds, pushed in real time*
- 历史趋势图（ECharts），Y 轴自适应 — *Trend chart with auto-scaling Y-axis*

### Smart Camera / 智能摄像头
- **Demo**：Pillow 模拟图片，可配置随机告警概率 — *Simulated images with configurable alert probability*
- **Own Pet**：OpenCV 采集，基于直方图相似度检测长时间静止 — *Histogram similarity-based inactivity detection*
- 手动刷新 + 自动定时抓拍 — *Manual refresh + auto capture*
- 相似度阈值和静止帧数均可通过网页配置 — *Thresholds configurable via web UI*

### Rule Engine / 规则引擎
- 高温警报（可配置阈值）— *High temperature alert (configurable)*
- 低湿警报（可配置阈值）— *Low humidity alert (configurable)*
- 摄像头静止检测 / 概率告警 — *Camera inactivity detection / probability alert*
- 告警入库并实时推送 — *Alerts persisted to DB and pushed in real time*

### Remote Control / 远程控制
- 喂食器远程触发 + 状态反馈 — *Feeder trigger with status feedback*
- 空调制冷开关 + 状态反馈 — *AC cooling on/off with status feedback*
- Toast 通知 + LED 状态指示 — *Toast notifications + status indicators*

### Real-time Dashboard / 实时仪表盘
- 温湿度数值 + 趋势图 — *Live values + trend chart*
- 最新抓拍图片 — *Latest snapshot*
- 警报列表（含缩略图）— *Alert list with thumbnails*
- WebSocket 自动推送 — *Auto-push via WebSocket*

### Security — MQTT Encryption / 安全 — MQTT 消息加密

所有传感器数据和摄像头消息在发布到公共 broker 前加密。*All sensor data and camera messages are encrypted before publishing to the public broker.*

**Algorithm / 加密算法：** SHA-256 stream cipher + HMAC-SHA256 authentication / SHA-256 流加密 + HMAC-SHA256 消息认证

**Standard library only — zero external dependencies / 纯标准库，零外部依赖：**

| Module / 模块 | Purpose / 用途 |
|---------------|----------------|
| `hashlib` | PBKDF2 key derivation + SHA-256 stream cipher / PBKDF2 密钥派生、SHA-256 流加密 |
| `hmac` | Message authentication (tamper-proof) / 消息认证码，防篡改 |
| `os` | Random salt & IV generation / 随机盐和 IV 生成 |
| `base64` | Ciphertext encoding / 密文编码传输 |

**Encryption scope / 加密范围：**

| Topic / 主题 | Encrypted / 加密 | Note / 说明 |
|--------------|-------------------|-------------|
| `demo/{pet_id}/sensor/*` | ✅ | Demo sensor data / 模拟传感器数据 |
| `demo/{pet_id}/camera/alert` | ✅ | Demo camera snapshots / 模拟摄像头抓拍 |
| `custom/{pet_id}/sensor/*` | ✅ | Real sensor data / 真实传感器数据 |
| `custom/{pet_id}/camera/alert` | ✅ | Real camera snapshots / 真实摄像头抓拍 |
| `pet/{pet_id}/control/*` | ❌ | Control commands — action strings only / 控制指令，仅动作字符串 |
| `system/pet/created` | ❌ | System notification — pet ID number only / 系统通知，仅数字 |

**Verify / 验证加密：** `python verify_encryption.py` — prints ciphertext from broker alongside decrypted plaintext. / 同时打印 broker 密文和解密明文。

---

## 📁 Project Structure / 项目结构

```
SmartPet/
├── config.py
├── database.py
├── publisher.py
├── subscriber.py
├── web_server.py
├── verify_encryption.py
├── start_all.bat
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── create_pet.html
│   └── manage_pets.html
├── utils/
│   ├── sensor_emulator.py
│   ├── camera_emulator.py
│   ├── real_sensor.py
│   ├── real_camera.py
│   ├── rule_engine.py
│   ├── crypto.py
│   ├── feeder.py
│   ├── ac.py
│   └── __init__.py
├── static/
└── README.md
```

| File | Role / 作用 |
|------|-------------|
| `config.py` | MQTT broker, topics, encryption key, thresholds — MQTT 配置、Topic 定义、加密密钥、默认阈值 |
| `database.py` | SQLite DB — pets, sensor data, alerts — 数据库操作（宠物、传感器、告警）|
| `publisher.py` | Publishes sensor + camera data — 发布端：传感器与摄像头数据采集 |
| `subscriber.py` | Rule engine, DB writer, executor — 订阅端：规则引擎、数据入库、执行器 |
| `web_server.py` | Flask + SocketIO web server + MQTT command dispatch — Web 服务 + MQTT 指令分发 |
| `verify_encryption.py` | Prints broker ciphertext vs decrypted plaintext — 加密验证工具 |
| `start_all.bat` | One-click launcher for Windows — Windows 一键启动 |
| `templates/` | Frontend pages — dashboard, create pet, manage pets — 前端页面 |
| `utils/sensor_emulator.py` | Simulated temp/humidity sensor — 模拟温湿度传感器 |
| `utils/camera_emulator.py` | Simulated camera (Pillow) — 模拟摄像头 |
| `utils/real_sensor.py` | Real DHT22 sensor driver — 真实 DHT22 传感器驱动 |
| `utils/real_camera.py` | Real USB camera driver (OpenCV) — 真实 USB 摄像头驱动 |
| `utils/rule_engine.py` | Rule engine — high temp, low humidity, inactivity detection — 规则引擎 |
| `utils/crypto.py` | MQTT encryption — stdlib only, zero dependencies — 加密模块 |
| `utils/feeder.py` | Feeder control — 喂食器控制 |
| `utils/ac.py` | AC control — 空调控制 |
| `static/` | Auto-created image storage — 自动创建，存放抓拍图片 |

---

## 🚀 Quick Start / 快速开始

### 1. Install Dependencies / 安装依赖

```bash
pip install paho-mqtt flask flask-socketio eventlet pillow
```

> Own Pet Mode on Raspberry Pi also requires / 树莓派 Own Pet 模式额外安装：
> `pip install adafruit-circuitpython-dht opencv-python`

> Encryption module uses Python stdlib only — **no extra dependencies**. / 加密模块仅用 Python 标准库，**无需额外依赖**。

### 2. Launch / 启动系统

Open three terminals in the project root / 打开三个终端，均在项目根目录：

| Terminal / 终端 | Command / 命令 | Role / 说明 |
|-----------------|----------------|-------------|
| 1 | `python subscriber.py` | 订阅端：接收数据、规则引擎、写库 |
| 2 | `python web_server.py` | Web 服务器 + SocketIO（端口 5000）|
| 3 | `python publisher.py` | 发布端：传感器与摄像头数据采集 |

> Windows users can double-click `start_all.bat` to launch all three at once. / Windows 用户可双击 `start_all.bat` 一键启动。

### 3. Open the Dashboard / 打开网页

**Local / 本机：** `http://127.0.0.1:5000`

**From other devices on the same LAN (e.g. Raspberry Pi) / 局域网内其他设备访问树莓派：**

```
http://<树莓派IP地址>:5000
```

> Run `hostname -I` on the Pi to find its IP, e.g. / 树莓派终端运行 `hostname -I` 获取 IP，如 `http://192.168.1.100:5000`

---

## 🖱️ Usage / 操作指南

### Demo Mode / 演示模式（默认）

- 预置 Fluffy（Cat）和 Buddy（Dog）两只演示宠物 — *Two demo pets pre-installed*
- 点击 **`+`** 创建更多模拟宠物，无需选择硬件 — *Click `+` to create more; no hardware selection needed*
- 点击 **齿轮图标** 修改温湿度告警阈值 — *Gear icon → edit alert thresholds*
- 点击 **相机图标** 调整随机告警概率 — *Camera icon → adjust alert probability*
- 点击遥控区按钮触发喂食器/空调，观察 Toast 反馈 — *Use remote control buttons for feeder & AC*

### Own Pet Mode / 真实宠物模式

- 切换到 Own Pet Mode 后点击 **`+`** 创建真实宠物 — *Switch to Own Pet, click `+`*
- 需要选择物理传感器和摄像头 — *Select physical sensor & camera*
- 相机设置中调整**相似度阈值**和**静止帧数** — *Configure similarity threshold & inactive frame limit*
- 连续静止帧数达标时触发摄像头告警 — *Alert triggers when consecutive similar frames reach limit*

### 验证加密 / Verify Encryption

```bash
python verify_encryption.py
```

Prints broker ciphertext vs decrypted plaintext side by side. / 同时打印 broker 密文和解密明文，对比验证。

---

## 🏗️ Architecture / 架构

```
┌──────────────┐     MQTT (encrypted/加密)  ┌──────────────┐
│  publisher   │ ──────────────────────────►│  subscriber  │
│  传感器采集   │      broker.emqx.io       │  规则引擎     │
│  摄像头抓拍   │                            │  数据入库     │
└──────┬───────┘                            └──────┬───────┘
       │                                           │
       │                                     SQLite DB
       │                                           │
       │                                   ┌───────┴──────┐
       └───────────────────────────────────│  web_server  │
                   MQTT (control/控制指令)  │  Flask       │
                                           │  SocketIO    │
                                           └──────┬───────┘
                                                  │
                                           WebSocket push
                                                  │
                                           ┌──────┴──────┐
                                           │  浏览器仪表盘  │
                                           └─────────────┘
```

---

## 🔧 Hardware Extension / 扩展硬件

Replace simulated modules in `utils/` with real hardware drivers. / 模拟模块集中在 `utils/` 下，替换即可接入真实硬件：

| Simulated / 模拟 | Replace with / 替换为 | Purpose / 用途 |
|------------------|----------------------|----------------|
| `sensor_emulator.py` | `real_sensor.py` (Adafruit DHT22) | Real temp & humidity / 真实温湿度 |
| `camera_emulator.py` | `real_camera.py` (OpenCV) | Real camera capture / 真实摄像头 |
| `feeder.py` | GPIO control | Physical feeder / 真实喂食器 |
| `ac.py` | GPIO / relay | Physical AC / 真实空调 |

No changes needed in subscriber, web_server, or dashboard. / 替换后其他模块无需修改。

### Multiple Devices / 接入多个设备

Each pet binds to its own sensor + camera pair. / 每个宠物绑定独立的传感器和摄像头：

- **Sensors / 传感器**：Add GPIO pins in `real_sensor.py` → `SENSOR_PIN_MAP`, e.g. `{1: board.D4, 2: board.D18, 3: board.D21}`
- **Cameras / 摄像头**：Add device indices in `real_camera.py` → `index_map`, e.g. `{2: 0, 3: 1, 4: 2}`
- **Registration / 注册**：List all devices in `database.py` → `get_devices()` for frontend selection / 在 `get_devices()` 中列出所有设备，前端即可选择
- Each Own Pet publishes to its own `custom/{pet_id}/` topic — no interference. / 每个宠物发布到独立的 topic，互不干扰

---

## 📄 License / 许可

MIT
