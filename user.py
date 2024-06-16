class User:
    """
    User object implementation.
    """
    def __init__(self, id_, speed, arr_loc, dep_loc, privacy_label, privacy_coeff, weights):
        """
        Initializes the user object.
        :param id_: Unique user id.
        :param speed: Movement speed (m/min.).
        :param arr_loc: Arrival location (x,y).
        :param dep_loc: Departure location (x,y).
        :param privacy_label: Privacy label (Privacy fundamentalists (1), privacy pragmatists (2), and privacy unconcerned (3)).
        :param privacy_coeff: Privacy coefficient (depends on label, for example see :func:`~scenarios.hospital.generate_scenario`.
        :param weights: Weights used in utility calculations (data vs energy trade-off).
        """
        self.id_ = id_
        self.speed = speed
        self.arr_loc = arr_loc
        self.dep_loc = dep_loc
        self.privacy_label = privacy_label
        self.privacy_coeff = privacy_coeff
        self.consent = 0  # 0 -> False, 1 -> True, >2 -> Number of rounds
        self.arr_time = 0.0
        self.dep_time = 0.0
        self.curr_loc = 0
        self.utility = 0.0
        self.norm_utility = 0.0
        self.power_consumed = 0.0
        self.time_spent = 0.0
        self.weights = weights

    def update_utility(self, utility):
        """
        Update user utility with the new utility.
        :param utility: The new utility value.
        """
        self.utility = utility

    def update_stand_utility(self, standardized_utility):
        """
        Update user utility with the new utility.
        :param utility: The new utility value.
        """
        self.standardized_utility = standardized_utility

    def update_location(self, curr_loc):
        """
        Update user location with the new/current location.
        :param curr_loc: The new location value (x,y).
        """
        self.curr_loc = curr_loc

    def update_arrival_time(self, arr_time):
        """
        Update/set user arrival time.
        :param arr_time: User arrival time.
        """
        self.arr_time = arr_time

    def update_departure_time(self, dep_time):
        """
        Update/set user departure time.
        :param dep_time: User departure time.
        """
        self.dep_time = dep_time

    def update_consent(self, consent):
        """
        Update user consent to represent if user has consented or not.
        :param consent: Boolean value for use consent (True or False).
        """
        self.consent = consent

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
        return (f"Object ID: {id(self)}, User ID: {self.id_}, Speed: {self.speed}, "
                f"Arrival Location: {self.arr_loc}, Departure Location: {self.dep_loc}, "
                f"Privacy Label: {self.privacy_label}, Privacy Coefficient: {self.privacy_coeff}, "
                f"Consent: {self.consent}, Utility: {self.utility}, Standardized Utility: {self.standardized_utility}, "
                f"Power Consumed: {self.power_consumed}, Time Spent: {self.time_spent}, "
                f"Weights: {self.weights}")

