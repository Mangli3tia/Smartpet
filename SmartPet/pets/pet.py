class Pet:
    def __init__(self, pet_id, sensors):
        self.pet_id = pet_id
        self.sensors = sensors

    def read_all(self):
        data = {}
        for name, sensor in self.sensors.items():
            data[name] = sensor.read()
        return data