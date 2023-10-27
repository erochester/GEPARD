from device import Device


class ESP32(Device):
    def __init__(self, tech):
        super().__init__(tech)

    def get_default_modes(self):
        # Define default mode values for each technology within the subclass
        if self.tech == "BLE":
            return {
                "Scanning": {"current": 0.132, "voltage": 5.09, "timing": 512},
                "Advertising": {"current": 0.128, "voltage": 5.09, "timing": 20.184},
                "Connected (Tx)": {"current": 0.128, "voltage": 5.09, "timing": 41.706},
                "Connected (Rx)": {"current": 0.092, "voltage": 5.09, "timing": 41.706},
            }
        elif self.tech == "WiFi":
            return {
                "Scan Mode (AP)": {"current": 0.162, "voltage": 5.09, "timing": 650},
                "Scan Mode (STA)": {"current": 0.144, "voltage": 5.09, "timing": 650},
                "Connection-Establishment Mode (AP)": {"current": 0.192, "voltage": 5.09, "timing": 0.2548},
                "Connection-Establishment Mode (STA)": {"current": 0.188, "voltage": 5.09, "timing": 0.238},
                "Transmit Mode": {"current": 0.212, "voltage": 5.09, "timing": 0.1},
                "Receive Mode": {"current": 0.168, "voltage": 5.09, "timing": 0.1},
            }

    def handle_mode(self, mode, payload_size=0):
        if mode in self.modes:
            current, voltage, timing = self.modes[mode]["current"], self.modes[mode]["voltage"], self.modes[mode][
                "timing"]
            extra_consumption = 0

            # TODO: check maximum packet sizes for technologies and adjust the extra consumption
            if "Tx" in mode and payload_size > 0:
                if self.tech == "BLE":
                    max_packet_size = 27  # Example maximum packet size for BLE
                    extra_consumption = (payload_size - max_packet_size) * 0.01  # Example extra consumption per byte
                elif self.tech == "WiFi":
                    max_packet_size = 1500  # Example maximum packet size for WiFi
                    extra_consumption = (payload_size - max_packet_size) * 0.005  # Example extra consumption per byte

                current += extra_consumption
                voltage += extra_consumption
                timing += extra_consumption

            print(f"ESP32 is in {self.tech} mode '{mode}':")
            print(f"Current: {current} A")
            print(f"Voltage: {voltage} V")
            print(f"Timing: {timing} ms")
        else:
            print(f"Mode '{mode}' is not supported for {self.tech} on ESP32.")
