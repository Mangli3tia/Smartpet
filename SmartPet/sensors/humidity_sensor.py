import random

class HumiditySensor:
    def read(self):
        return round(random.uniform(40.0, 70.0), 1)