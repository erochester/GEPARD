import math


class Lora:

    def __init__(self):
        self.voltage = 3.3
        self.i_rx = 11.2  # mA
        self.cr = 4 / 5
        # initial values
        # are adjusted during each send and receive
        self.lora_max_payload = 51
        self.sf = 10
        self.bw = 250
        self.i_tx = 125  # mA

    def send(self, payload):

        # determine lora mode to use
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / self.bw
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            n_phy = 8 + max(math.ceil((28 + 8 * (payload - self.lora_max_payload) + 4 * self.sf) /
                                      (4 * self.sf)) * (self.cr + 4), 0)
            t_phy = t_sym * n_phy
            t_temp_tx = t_pre + t_phy
            t_tx = t_temp_tx

        n_phy = 8 + max(math.ceil((28 + 8 * self.lora_max_payload + 4 * self.sf) /
                                  (4 * self.sf)) * (self.cr + 4), 0)
        t_phy = t_sym * n_phy
        t_temp_tx = t_pre + t_phy
        t_tx += t_temp_tx

        return t_tx / 3600 * self.voltage * self.i_tx / 1000, t_tx

    def receive(self, payload):
        # TODO: there is no difference between send and receive
        # determine lora mode to use
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / self.bw
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            n_phy = 8 + max(math.ceil((28 + 8 * (payload - self.lora_max_payload) + 4 * self.sf) /
                                      (4 * self.sf)) * (self.cr + 4), 0)
            t_phy = t_sym * n_phy
            t_temp_tx = t_pre + t_phy
            t_tx = t_temp_tx

        n_phy = 8 + max(math.ceil((28 + 8 * self.lora_max_payload + 4 * self.sf) /
                                  (4 * self.sf)) * (self.cr + 4), 0)
        t_phy = t_sym * n_phy
        t_temp_tx = t_pre + t_phy
        t_tx += t_temp_tx

        return t_tx / 3600 * self.voltage * self.i_tx / 1000, t_tx

    def determine_mode(self, payload):
        # the pp size determines the mode we will use
        if payload <= 51:
            self.lora_max_payload = 51
            self.sf = 10
            self.bw = 250
            self.i_tx = 125
        elif 51 < payload <= 115:
            self.lora_max_payload = 115
            self.sf = 9
            self.bw = 250
            self.i_tx = 90
        else:
            self.lora_max_payload = 242
            self.sf = 7
            self.bw = 500
            self.i_tx = 28
