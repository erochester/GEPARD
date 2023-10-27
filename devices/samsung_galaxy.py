from device import Device

class Samsung_Galaxy(Device):
    def __init__(self, tech):
        super().__init(tech)

    def get_default_modes(self):
        # Define default mode values for each technology within the subclass
        if self.tech == "BLE":
            return {
                "Scanning": {"current": 0.057, "voltage": 4.33, "timing": 512},
                "Advertising": {"current": 0.047, "voltage": 4.33, "timing": 1000.184},
                "Connected (Tx)": {"current": 0.05, "voltage": 4.33, "timing": 9.206},
                "Connected (Rx)": {"current": 0.048, "voltage": 4.33, "timing": 9.206},
            }
        elif self.tech == "WiFi":
            return {
                "Scan Mode (AP)": {"current": 0.25, "voltage": 4.33, "timing": 520},
                "Scan Mode (STA)": {"current": 0.06, "voltage": 4.33, "timing": 520},
                "Connection-Establishment Mode (AP)": {"current": 0.25, "voltage": 4.33, "timing": 0.0655},
                "Connection-Establishment Mode (STA)": {"current": 0.25, "voltage": 4.33, "timing": 0.061},
                "Transmit Mode": {"current": 0.25, "voltage": 4.33, "timing": 0.028},
                "Receive Mode": {"current": 0.06, "voltage": 4.33, "timing": 0.028},
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

            print(f"Samsung Galaxy is in {self.tech} mode '{mode}':")
            print(f"Current: {current} A")
            print(f"Voltage: {voltage} V")
            print(f"Timing: {timing} ms")
        else:
            print(f"Mode '{mode}' is not supported for {self.tech} on Samsung Galaxy.")