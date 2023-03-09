from ble import BLE
from lora import Lora


class Network:
    def __init__(self, tech, logger):
        self.logger = logger
        self.tech = tech
        if tech == "ble":
            self.technology = BLE()
        elif tech == "lora":
            self.technology = Lora()

    def send(self, payload):
        return self.technology.send(payload)

    def receive(self, payload):
        return self.technology.receive(payload)
