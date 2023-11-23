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