import math

"""This class assumes that packets are sent using the TCP protocol and have a maximum payload size of 1500 bytes. The 
send() method calculates the time taken to transmit the payload based on the number of packets needed to send it and 
a time delay between packets. The receive() method calculates the time taken to receive the payload based on the same 
assumptions as the send() method, as well as the time spent performing Clear Channel Assessment (CCA) to avoid 
collisions with other WiFi transmissions."""
class WiFi:

    def __init__(self):
        self.voltage = 3.7
        self.i_rx = 90  # mA
        self.i_tx = 1800  # mA
        self.cca_busy_ratio = 0.2  # ratio of time busy during CCA
        self.time_between_packets = 0.1  # in seconds

    def send(self, payload):
        packet_num = math.ceil(payload / 1500)
        t_tx = packet_num * self.time_between_packets
        return t_tx / 3600 * self.voltage * self.i_tx / 1000, t_tx

    def receive(self, payload):
        packet_num = math.ceil(payload / 1500)
        t_rx = packet_num * self.time_between_packets
        t_cca = t_rx * self.cca_busy_ratio
        return t_rx / 3600 * self.voltage * self.i_rx / 1000, t_rx + t_cca
