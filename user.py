class User:

    def __init__(self, id_, speed, arr_loc, dep_loc, privacy_label, privacy_coeff):
        self.id_ = id_
        self.speed = speed
        self.arr_loc = arr_loc
        self.dep_loc = dep_loc
        self.privacy_label = privacy_label
        self.privacy_coeff = privacy_coeff
        self.consent = False
        self.arr_time = 0
        self.dep_time = 0
        self.curr_loc = 0

    def update_location(self, curr_loc):
        self.curr_loc = curr_loc

    def update_arrival_time(self, arr_time):
        self.arr_time = arr_time

    def update_departure_time(self, dep_time):
        self.dep_time = dep_time

    def update_consent(self, consent):
        self.consent = consent

    def __str__(self):
        return f"User ID: {self.id_}, Speed: {self.speed}, Arrival Location: {self.arr_loc}, " \
               f"Departure Location: {self.dep_loc}, Privacy Label: {self.privacy_label}, " \
               f"Privacy Coefficient: {self.privacy_coeff}, Consent: {self.consent}"
