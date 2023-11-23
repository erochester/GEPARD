from devices.esp32 import ESP32
from devices.samsung_galaxy import Samsung_Galaxy


class Network:
    def __init__(self, tech, device_type, logger):
        # TODO: add device types to other technologies and remove lora for now?
        self.logger = logger
        self.tech = tech
        self.device_type = device_type
        # TODO: for now there is not LoRa
        if self.device_type == "esp32":
            self.technology = ESP32(tech)
        elif self.device_type == "samsung_galaxy":
            self.technology = Samsung_Galaxy(tech)
