class BLE:
    def __init__(self):
        self.current = {}
        self.time = {}
        self.voltage = {}

    def send(self, mode, payload_size, time_in_seconds):
        if mode not in self.current:
            raise ValueError(f"Invalid BLE mode: {mode}")

        current = self.current[mode]

        # Calculate power consumption for sending in Watts
        power_watts = (current * self.voltage * time_in_seconds) * (payload_size / 251)

        # Calculate power consumption in Watt-hours
        power_wh = power_watts / 3600  # Convert from Watt-seconds to Watt-hours
        return power_wh

    def receive(self, mode, payload_size, time_in_seconds):
        if mode not in self.current:
            raise ValueError(f"Invalid BLE mode: {mode}")

        current = self.current[mode]

        # Calculate power consumption for receiving in Watts-seconds
        power_watts = (current * self.voltage * time_in_seconds) * (payload_size / 251)

        # Calculate power consumption in Watt-hours
        power_wh = power_watts / 3600  # Convert from Watts to Watt-hours
        return power_wh


class ESP32_BLE(BLE):
    def __init__(self):
        super().__init__()
        self.current["Scanning"] = 0.132
        self.time["Scanning"] = 512 / 1000  # Convert from milliseconds to seconds
        self.current["Advertising"] = 0.128
        self.time["Advertising"] = 20.184 / 1000  # Convert from milliseconds to seconds
        self.current["Connected"] = 0.128
        self.time["Connected"] = 41.706 / 1000  # Convert from milliseconds to seconds
        self.voltage = 5.09


class Samsung_Galaxy_BLE(BLE):
    def __init__(self):
        super().__init__()
        self.current["Scanning"] = 0.049
        self.time["Scanning"] = 512 / 1000  # Convert from milliseconds to seconds
        self.current["Advertising"] = 0.047
        self.time["Advertising"] = 1000.184 / 1000  # Convert from milliseconds to seconds
        self.current["Connected"] = 0.057
        self.time["Connected"] = 9.206 / 1000  # Convert from milliseconds to seconds
        self.voltage = 4.33
