class IoTDevice:
    def __init__(self, device_location):
        self.device_location = device_location

    def __str__(self):
        return f"Device Location: {self.device_location}"
