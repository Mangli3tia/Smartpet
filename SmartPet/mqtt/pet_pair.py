from pets.pet import Pet
from sensors.temp_sensor import TempSensor
from sensors.activity_sensor import ActivitySensor
from sensors.humidity_sensor import HumiditySensor

pet_list = [
    Pet("bai", {
        "temp": TempSensor(),
        "active": ActivitySensor()
    }),
    Pet("hei", {
        "temp": TempSensor(),
        "humidity": HumiditySensor()
    }),
    Pet("hua", {
        "temp": TempSensor(),
        "active": ActivitySensor(),
        "humidity": HumiditySensor()
    })
]