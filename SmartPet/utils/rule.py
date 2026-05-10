from config.threshold import TEMP_WARN

# 真正规则引擎格式：
# 传感器, 条件, 阈值, 要执行的动作函数
rules = [
    ("temp", ">", TEMP_WARN, "alert_high_temp"), 
]