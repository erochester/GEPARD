class IoTDevice:
    """
    IoT Device implementation.
    """
    def __init__(self, device_location):
        """
        Initialize the utilities, weights for calculations and device location in the space.
        :param device_location: Device location in the space (x,y).
        """
        self.device_location = device_location
        self.utility = 0
        self.weights = []

    def update_weights(self, weights):
        """
        Updates the weights/coefficients to new values (data vs energy trade-off).
        :param weights: New weight values [w1, w2].
        """
        self.weights = weights

    def update_utility(self, utility):
        """
        Updates the utility to new value.
        :param utility: New utility value.
        """
        self.utility = utility

    def __str__(self):
        return f"Device Location: {self.device_location}"
