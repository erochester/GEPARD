class IoTDevice:
    def __init__(self, device_location):
        self.device_location = device_location
        self.utility = 0
        self.weights = []

    def update_weights(self, weights):
        self.weights = weights

    def update_utility(self, utility):
        self.utility = utility

    def __str__(self):
        return f"Device Location: {self.device_location}"
