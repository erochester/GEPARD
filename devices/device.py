class Device:
    def __init__(self, tech):
        self.tech = tech
        self.modes = self.get_default_modes()

    def set_mode_values(self, mode, current, voltage, timing):
        if mode in self.modes:
            self.modes[mode] = {
                "current": current,
                "voltage": voltage,
                "timing": timing
            }
        else:
            print(f"Mode '{mode}' is not supported for this device.")

    def get_mode_values(self, mode):
        if mode in self.modes:
            return self.modes[mode]
        else:
            print(f"Mode '{mode}' is not supported for this device.")
            return None

    def get_default_modes(self):
        # This method is implemented in subclasses to define technology-specific modes.
        pass

    def handle_mode(self):
        # This method is implemented in subclasses to define how to handle technology-specific modes.
        pass