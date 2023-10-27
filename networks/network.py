from networks.ble import BLE, ESP32_BLE, Samsung_Galaxy_BLE
from networks.lora import Lora
from networks.wifi import WiFi
from devices.esp32 import ESP32
from devices.device import Device


class Network:
    def __init__(self, tech, device_type, logger):
        # TODO: add device types to other technologies and remove lora for now?
        self.logger = logger
        self.tech = tech
        # TODO: for now there is not LoRa
        if self.device_type == "esp32":
            self.technology = ESP32(tech)
        elif self.device_type == "samsung_galaxy":
            self.technology = Samsung_Galaxy(tech)

    # TODO: move these deeper into ESP32 and Samsung modules,
    #  since not every module will have all of the functionalities.
    # def send(self, payload):
    #     return self.technology.send(payload)
    #
    # def receive(self, payload):
    #     return self.technology.receive(payload)
