from utils.rule import rules
from utils import action


def check_and_run(sensor_type, value, pet_id):
    val = float(value)

    # 遍历所有规则（一条通用逻辑）
    for sensor, op, threshold, action_name in rules:
        if sensor != sensor_type:
            continue

        # 通用比较
        if op == ">":
            triggered = val > threshold
        elif op == "<":
            triggered = val < threshold
        else:
            triggered = False

        if triggered:
            # 🔥 直接运行动作，不需要在handler写if
            action_func = getattr(actions, action_name)
            action_func(pet_id)