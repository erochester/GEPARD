import math
from util import get_config

class LoRa:
    """
    Implements LoRa networks. We assume Class A LoRa device.
    """
    def __init__(self):
        """
        Initialize the maximum payload, assumed maximum effective communication distance, voltage
        and current consumption and other variables.
        """
        self.config = get_config()['Lora'] # load lora config
        self.voltage = self.config['voltage']
        self.i_rx = self.config['i_rx']  # mA
        self.cr = self.config['cr']
        # initial values
        # are adjusted during each send and receive
        self.lora_max_payload = self.config['lora_max_payload']  # bytes
        self.sf = self.config['sf']
        self.bw = self.config['bw'] # kHz
        self.i_tx = self.config['i_tx']  # mA
        self.comm_distance = self.config['comm_distance']  # m assume 10 km for lora

    def send(self, payload):
        """
        Method to calculate power and time consumption when sending packet with specific payload size.
        :param payload: Payload size to send (bytes)
        :return: Returns power and time consumption (W and s).
        """
        # determine lora mode to use
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / (self.bw*1000)
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            while payload - self.lora_max_payload > 0:
                payload = payload - self.lora_max_payload
                n_phy = 8 + max(math.ceil((28 + 8 * (payload) + 4 * self.sf) /
                                          (4 * self.sf)) * (self.cr + 4), 0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx += t_temp_tx

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
        # Note that there is practically no difference between send and receive
        # determine lora mode to use
        self.determine_mode(payload)
        # How many packets to send
        packet_num = math.ceil(payload / self.lora_max_payload)

        t_tx = 0
        t_sym = (2 ** self.sf) / (self.bw*1000)
        t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
        # does the payload fit into 1 packet?
        if packet_num > 1:
            while payload - self.lora_max_payload > 0:
                payload = payload - self.lora_max_payload
                n_phy = 8 + max(math.ceil((28 + 8 * (self.lora_max_payload) + 4 * self.sf) /
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
        # Initialize variables to store the best mode (lowest ToA)
        best_sf = self.sf
        best_bw = self.bw
        best_toa = float('inf')

        # Define SF/BW configurations and their respective max payload sizes and i_tx (mA)
        # Access the mode_configs data
        mode_configs = {(tuple(item[0])): item[1] for item in self.config['mode_configs']}

        # Loop through possible SF and BW combinations to minimize Time on Air (ToA)
        for sf, bw in mode_configs.keys():  # Use only the defined combinations
            bw_hz = bw * 1000
            t_sym = (2 ** sf) / bw_hz
            t_pre = t_sym * 4.25

            n_phy = 8 + max(math.ceil((28 + 8 * payload + 4 * sf) /
                                      (4 * sf)) * (self.cr + 4), 0)
            t_phy = t_sym * n_phy
            t_tx = t_pre + t_phy

            # Update the mode if this combination gives lower ToA
            if t_tx < best_toa:
                best_toa = t_tx
                best_sf = sf
                best_bw = bw

        # Set the best mode and corresponding parameters
        self.sf = best_sf
        self.bw = best_bw
        self.lora_max_payload = mode_configs[(best_sf, best_bw)]["lora_max_payload"]
        self.i_tx = mode_configs[(best_sf, best_bw)]["i_tx"]
