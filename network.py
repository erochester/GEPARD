from ble import BLE


class Network:
    def __init__(self, tech, logger):
        self.logger = logger
        self.tech = tech
        if tech == "ble":
            self.technology = BLE()

    def send(self, payload):
        return self.technology.send(payload)

    def receive(self, payload):
        return self.technology.receive(payload)
