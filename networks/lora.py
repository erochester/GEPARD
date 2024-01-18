import math


class LoRa:
    """
    Implements LoRa networks. We assume Class A LoRa device.
    """
    def __init__(self):
        """
        Initialize the maximum payload, assumed maximum effective communication distance, voltage
        and current consumption and other variables.
        """
        # mA reference:
        # https://cdn.cnx-software.com/wp-content/uploads/2018/03/LoRaWAN-vs-NB-IoT-LTE-Cat-M1-Power-Consumption.jpg?lossy=0&strip=none&ssl=1
        self.voltage = 3.3  # V
        self.i_rx = 12  # mA
        self.cr = 4 / 5
        # initial values
        # are adjusted during each send and receive
        self.lora_max_payload = 51  # bytes
        self.sf = 10
        self.bw = 250
        self.i_tx = 24  # mA
        self.comm_distance = 10000  # m assume 10 km for lora

    def send(self, payload):
        """
        Method to calculate power and time consumption when sending packet with specific payload size.
        :param payload: Payload size to send (bytes)
        :return: Returns power and time consumption (W and s).
        """
        # determine lora mode to use
        # TODO: adding 12 bytes as an overhead per packet
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / self.bw
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            while payload - self.lora_max_payload > 0:
                payload = payload - self.lora_max_payload
                n_phy = 8 + max(math.ceil((28 + 8 * (payload) + 4 * self.sf) /
                                          (4 * self.sf)) * (self.cr + 4), 0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx = t_temp_tx

        n_phy = 8 + max(math.ceil((28 + 8 * payload + 4 * self.sf) /
                                  (4 * self.sf)) * (self.cr + 4), 0)
        t_phy = t_sym * n_phy
        t_temp_tx = t_pre + t_phy
        t_tx += t_temp_tx

        return (t_tx / 3600) * self.voltage * (self.i_tx / 1000), t_tx

    def receive(self, payload):
        """
        Method to calculate power and time consumption when receiving packet with specific payload size.
        :param payload: Payload size to receive (bytes)
        :return: Returns power and time consumption (W and s).
        """
        # TODO: there is no difference between send and receive
        # determine lora mode to use
        # TODO: adding 12 bytes as an overhead per packet
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / self.bw
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            while payload - self.lora_max_payload > 0:
                payload = payload - self.lora_max_payload
                n_phy = 8 + max(math.ceil((28 + 8 * (payload) + 4 * self.sf) /
                                          (4 * self.sf)) * (self.cr + 4), 0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx = t_temp_tx

        n_phy = 8 + max(math.ceil((28 + 8 * payload + 4 * self.sf) /
                                  (4 * self.sf)) * (self.cr + 4), 0)
        t_phy = t_sym * n_phy
        t_temp_tx = t_pre + t_phy
        t_tx += t_temp_tx

        return (t_tx / 3600) * self.voltage * (self.i_rx / 1000), t_tx

    def determine_mode(self, payload):
        """
        Determine the LoRa mode to use (i.e., SF/BW combination) based on the payload.
        Simple implementation of Adaptive Data Rate (ADR).
        :param payload: Payload size in bytes.
        """
        # the pp size determines the mode we will use
        if payload <= 51:
            self.lora_max_payload = 51  # bytes
            self.sf = 10
            self.bw = 250
            self.i_tx = 125
        elif 51 < payload <= 115:
            self.lora_max_payload = 115  # bytes
            self.sf = 9
            self.bw = 250
            self.i_tx = 90
        else:
            self.lora_max_payload = 242  # bytes
            self.sf = 7
            self.bw = 500
            self.i_tx = 28
