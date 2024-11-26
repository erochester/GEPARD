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
        self.power_consumed = 0
        self.time_spent = 0
        self.utility = 0
        self.standardized_utility = 0
        self.norm_utility = 0
        self.weights = []
        self.offers = []

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

    def update_stand_utility(self, standardized_utility):
        """
        Update user utility with the new utility.
        :param standardized_utility: The new utility value.
        """
        self.standardized_utility = standardized_utility

    def add_to_time_spent(self, time_spent):
        """
        Add to time spent.
        :param time_spent: The time spent on negotiation.
        """
        self.time_spent += time_spent

    def add_to_power_consumed(self, power_consumed):
        """
        Add to power consumed.
        :param power_consumed: The power consumed on negotiation.
        """
        self.power_consumed += power_consumed

    def add_to_utility(self, utility):
        """
        Add to utility.
        :param utility: The utility of the negotiation.
        """
        self.utility += utility

    def __str__(self):
        return f"Device Location: {self.device_location}"
