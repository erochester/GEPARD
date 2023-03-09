import math


class BLE:

    def __init__(self):
        self.max_payload_size = 251
        self.tx_power_consumption = 84
        self.rx_power_consumption = 66
        self.ifs_power_consumption = 45
        # Processing power consumption values change according to the processing done
        # pre-processing power consumption is 15mW
        self.pre_power_consumption = 15
        # post-processing power consumption is 24mW
        self.post_power_consumption = 24

    def send(self, payload):
        power_consumed = 0
        # How many packets to send
        packet_num = math.ceil(payload / self.max_payload_size)
        power_consumed += self.pre_power_consumption + packet_num * self.tx_power_consumption + \
                          (
                                  packet_num - 1) * self.ifs_power_consumption + self.post_power_consumption
        return power_consumed

    def receive(self, payload):
        power_consumed = 0
        # How many packets to receive
        packet_num = math.ceil(payload / self.max_payload_size)
        power_consumed += self.pre_power_consumption + packet_num * self.rx_power_consumption + \
                          (
                                  packet_num - 1) * self.ifs_power_consumption + self.post_power_consumption
        return power_consumed
