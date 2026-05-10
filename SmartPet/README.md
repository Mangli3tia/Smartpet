# SmartPet
智能宠物监测系统 —— 基于 MQTT 模拟传感器数据发布与订阅

## 结构
- sensors: 传感器模拟（温度、活动量、湿度）
- pets: 宠物主体类
- mqtt: MQTT 发布端、订阅端、宠物与传感器配对
- utils: 数据库与消息处理
- config: 项目配置

## 运行
```bash
pip install -r requirements.txt

# 启动发布端
python mqtt/publisher.py

# 启动订阅端
python mqtt/subscriber.py

#sensors/temp_sensor.py
**作用：温度传感器模拟**
- 生成模拟温度数据（38.0~40.0℃）
- 提供 read() 方法获取当前温度

#sensors/activity_sensor.py
**作用：活动量传感器模拟**
- 生成模拟活动量数据（20~100）
- 提供 read() 方法获取当前活动量

#sensors/humidity_sensor.py
**作用：湿度传感器模拟**
- 生成模拟环境湿度数据（40~70%）
- 提供 read() 方法获取当前湿度

#pets/pet.py
**作用：宠物实体类**
- 定义一只宠物拥有哪些传感器
- 提供 read_all() 方法一次性读取所有传感器数据

#mqtt/pet_pair.py
**作用：宠物与传感器配对**
- 创建 3 只宠物：bai、hei、hua
- 给每只宠物分配不同传感器组合
- 供发布端循环读取数据

#mqtt/publisher.py
**作用：MQTT 发布端**
- 循环读取每只宠物的传感器数据
- 按照主题格式发送到 MQTT 服务器
- 包含 on_connect、on_publish 回调函数
- 每 2 秒发布一次数据

#mqtt/subscriber.py
**作用：MQTT 订阅端（核心入口）**
- 订阅所有宠物的传感器数据
- 收到消息后拆分出宠物ID、传感器类型、数值
- 分别交给：handler 告警 + database 存库

#utils/handler.py
**作用：温度告警与数据打印**
- 接收订阅端传来的数据
- 打印宠物信息与传感器值
- 判断温度是否超标，超标则告警

#utils/database.py
**作用：数据库操作**
- 初始化数据库表
- 保存宠物数据（包含宠物ID、时间、传感器类型、值）
- 每条数据独立存储，可区分每只宠物