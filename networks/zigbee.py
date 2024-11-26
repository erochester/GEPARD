from util import get_config


class ZigBee:
    """
    Implements ZigBee networks.
    We consider the best case scenario without retransmissions and collisions. Non-beacon setup.
    Reference: Modelling of Current Consumption in 802.15.4/ZigBee Sensor Motes (E. Casilari et al.)
    """
    def __init__(self):
        """
        Specifies operating voltage, ACK packet size and effective communication distance.
        """
        self.config = get_config()['Zigbee']  # load Zigbee config
        self.voltage = self.config['voltage']  # V
        self.ack_size = self.config['ack_size']  # bytes
        self.comm_distance = self.config['comm_distance']  # m effective communication distance for ZigBee

    def startup(self):
        """
        Used to account for radio startup power and time consumptions.
        :return: Power and time consumed (W and s).
        """
        # 2 mA as per reference. Power-up microcontroller.
        total_power_consumed = 2 * self.voltage  # mW

        # convert to W
        total_power_consumed = total_power_consumed / 1000

        total_duration = 1100  # ms

        # convert to seconds
        total_duration = total_duration / 1000

        return total_power_consumed, total_duration

    def association(self):
        """
        Used to account for association process power and time consumptions.
        :return: Power and time consumed (W and s).
        """
        # We simplify association modelling by assuming that Coordinator consumes same amount of power and time as mote

        # Scanning in 1 channel
        total_power_consumed = 26.6 * self.voltage  # mW

        # convert to W
        total_power_consumed = total_power_consumed / 1000

        total_duration = 2000  # ms

        # convert to seconds
        total_duration = total_duration / 1000

        return total_power_consumed, total_duration

    def send(self, payload):
        """
        Used to account for sending a packet of payload size power and time consumptions.
        :param payload: payload size (bytes)
        :return: Power and time consumed (W and s).
        """
        t_tx = (8 * (31 + payload)) / 250000  # s, where 250000 is the data rate in bps

        t_onoff = self.config['t_onoff']
        i_onoff = self.config['i_onoff']
        t_list = self.config['t_list']
        i_list = self.config['i_list']
        i_tx = self.config['i_tx']

        total_duration = t_tx + t_onoff + t_list

        total_current_consumption = ((t_onoff * i_onoff) + (t_list * i_list) + (t_tx * i_tx)) / total_duration

        total_power_consumed = total_current_consumption * self.voltage  # W

        return total_power_consumed, total_duration

    def receive(self, payload):
        """
        Used to account for receiving a packet of payload size power and time consumptions.
        :param payload: payload size (bytes)
        :return: Power and time consumed (W and s).
        """
        t_rx = (8 * (31 + payload)) / 250000  # s

        t_onoff = self.config['t_onoff']
        i_onoff = self.config['i_onoff']
        i_rx = self.config['i_rx']

        t_tx = (8 * (31 + 11)) / 250000  # s, where 250000 is the data rate in bps and 11 bytes is the ACK

        i_tx = self.config['i_tx']

        # No need for listening because 802.15.4 sets up a constant 'quiet' period after a transmission

        total_duration = t_rx + t_onoff + t_tx  # s

        total_current_consumption = ((t_onoff * i_onoff) + (t_rx * i_rx) + (t_tx * i_tx)) / total_duration  # A

        total_power_consumed = total_current_consumption * self.voltage  # W

        return total_power_consumed, total_duration
