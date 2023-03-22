import math


class BLE:

    def __init__(self):
        self.max_payload_size = 251  # bytes

        self.voltage = 3.3
        self.i_tx = 25  # mA
        self.i_pre = 1  # mA
        self.i_post = 1  # mA
        self.i_ifs = 0.002  # mA
        self.i_rx = 0.01  # mA

        self.data_rate = 1000000  # 1Mbps

        time_tx_rx = (8 * self.max_payload_size) / self.data_rate

        self.t_pre = 1  # ms
        self.t_post = 1  # ms
        self.t_ifs = 0.15  # ms
        self.t_tx = time_tx_rx * 1000  # ms
        self.t_rx = time_tx_rx * 1000  # ms

    def send(self, payload):
        power_consumed = 0
        time_spent = 0
        # How many packets to send
        packet_num = math.ceil(payload / self.max_payload_size)
        power_consumed += (self.t_pre / 1000 * self.voltage * self.i_pre / 1000) + \
                          (packet_num * self.t_tx / 1000 * self.voltage * self.i_tx / 1000) + (
                                      (packet_num - 1) * self.t_ifs / 1000 * self.voltage *
                                      self.i_ifs / 1000) + (self.t_post / 1000 * self.voltage * self.i_post / 1000)
        time_spent += (self.t_pre / 1000) + (packet_num * self.t_tx / 1000) + (
                    (packet_num - 1) * self.t_ifs / 1000) + (self.t_post / 1000)

        return power_consumed, time_spent

    def receive(self, payload):
        power_consumed = 0
        time_spent = 0
        # How many packets to receive
        packet_num = math.ceil(payload / self.max_payload_size)
        power_consumed += (self.t_pre / 1000 * self.voltage * self.i_pre / 1000) + \
                            (packet_num * self.t_rx / 1000 * self.voltage * self.i_rx / 1000) + (
                                        (packet_num - 1) * self.t_ifs / 1000 * self.voltage *
                                        self.i_ifs / 1000) + (self.t_post / 1000 * self.voltage * self.i_post / 1000)
        time_spent += (self.t_pre / 1000) + (packet_num * self.t_rx / 1000) + (
                    (packet_num - 1) * self.t_ifs / 1000) + (self.t_post / 1000)

        return power_consumed, time_spent
