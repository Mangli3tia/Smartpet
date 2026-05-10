import random

class TempSensor:
    def read(self):
        return round(random.uniform(38.0, 40.0), 1)