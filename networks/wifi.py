import random

# UDP payloads
# Samsung Galaxy Note 10.1 @ 1GHz, 6 Mbps and 6 dBm as a reference
# One to one comms

# TODO: Add device discovery and connection establishment or assume D2D communication

"""
We assume WiFi Direct that follows the following sequence of frames and their sizes:
| Sequence Step                           | Sender                        | Frame Type               | Assumed Frame Size Range (Bytes) | Assumed Average Frame Size (Bytes) | Assumption                                                                                             |
|-----------------------------------------|-------------------------------|--------------------------|---------------------------------|------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Connection Establishment**            |                               |                          |                                 |                                    |                                                                                                         |
| 1. Probe Request                        | Smartphone (Group Owner)      | Probe Request            | ~26-28                           | ~27                                | Assumption: Probe Request frame includes basic information about the sender's capabilities and intent to connect.                                                |
| 2. Probe Response                       | IoT Device                    | Probe Response           | ~26-28                           | ~27                                | Assumption: Probe Response frame is a confirmation from the IoT device indicating its presence and readiness to connect.                                          |
| 3. Association Request                  | Smartphone (Group Owner)      | Association Request      | ~30-32                           | ~31                                | Assumption: Association Request frame includes details about the connection request, capabilities, and requirements.                                              |
| 4. Association Response                 | IoT Device                    | Association Response     | ~30-32                           | ~31                                | Assumption: Association Response frame is a confirmation from the IoT device indicating acceptance or rejection of the request.                                     |
| 5. Group Owner Negotiation              | Both Devices                  | Group Owner Negotiation  | ~40-60                           | ~50                                | Assumption: Frames exchanged during negotiation may include negotiation parameters, introducing variability.                                                  |
   - Frames Sent by Smartphone            | Smartphone (Group Owner)      | Negotiation Frames       | ~40-60                           | ~50                                | Assumption: The smartphone initiates the negotiation process by sending negotiation frames.                                                                      |
   - Frames Sent by IoT Device            | IoT Device                    | Negotiation Response     | ~40-60                           | ~50                                | Assumption: The IoT device responds to the negotiation frames from the smartphone.                                                                                 |
| 6. Group Formation                       | Both Devices                  | Group Formation          | ~40-60                           | ~50                                | Assumption: Group formation frames may include information about the group, contributing to variability.                                                          |
   - Frames Sent by Smartphone            | Smartphone (Group Owner)      | Formation Frames         | ~40-60                           | ~50                                | Assumption: The smartphone potentially sends frames related to group formation, announcing its intent or parameters.                                               |
   - Frames Sent by IoT Device            | IoT Device                    | Formation Response       | ~40-60                           | ~50                                | Assumption: The IoT device responds to the frames from the smartphone, acknowledging or providing additional information for group formation.                          |
|                                         |                               |                          |                                 |                                    |                                                                                                         |
| **Privacy Policy Transmission**         |                               |                          |                                 |                                    |                                                                                                         |
| 7. Data Frames                         | Smartphone (Group Owner)      | Data Frames              | ~100-150                         | ~125                               | Assumption: Data frames carrying the payload (privacy policy) may vary in size based on the payload length and protocol overhead.                                       |
| 8. Data Frames Acknowledgment          | IoT Device                    | Acknowledgment Frames    | ~40-60                           | ~50                                | Assumption: Acknowledgment frames may include acknowledgment information and have a size within a certain range.                                                      |
"""

class WiFi:

    def __init__(self):
        self.mac_preamble_size = 20  # bytes
        self.plcp_header_size = 24  # bytes (transmitted at basic rate of 1 or 6 Mbps) We choose 6 Mbps.
        self.udp_header_size = 8  # bytes
        self.ip_header_size = 20  # bytes

        self.probe_request_size = 27  # bytes
        self.probe_response_size = 27  # bytes
        self.association_request_size = 31  # bytes
        self.association_response_size = 31  # bytes
        self.group_owner_negotiation_size = 50  # bytes
        self.group_owner_negotiation_response_size = 50  # bytes
        self.group_formation_size = 50  # bytes
        self.group_formation_response_size = 50  # bytes
        self.action_frames_size = 50  # bytes
        self.wifi_direct_invitation_size = 50  # bytes
        self.wifi_direct_invitation_response_size = 50  # bytes
        self.acknowledgment_frames_size = 50  # bytes

        self.dwell_time = 0.12  # (s) dwell time

        self.transmission_rate = 6 * 10 ^ 6  # bps

        self.idle_consumption = 506.74  # (mW) idle consumption \rho_id
        # frame generation rate (keep below saturation) \lambda_g

        self.tx_consumption = 604.2  # (mW) transmission consumption

        self.rx_consumption = 24.51  # (mW) reception consumption
        self.cross_factor = 0.074  # (mJ) frame processing energy toll (cross_factor) \gamma_g
        self.cross_factor_rx = 0.059  # (mJ) cross_factor in reception \gamma_xr

    def wifi_consumption_model_ce(self, group_owner_or_not):
        """
        Wifi energy consumption and time model for group owner and other UE for connection establishment
        :param group_owner_or_not:  (bool) True if the device is group owner, False otherwise
        :return:
        """

        total_power_consumed = 0
        total_duration = 0

        # if group owner
        if group_owner_or_not:
            # total energy consumption of the device in the discovery phase
            # we assume the probability of discovering the UE in a given cycle is 1/3
            probability_discovery = 1 / 3
            # the number of listening cycles then is 1/p
            number_of_listening_cycles = 1 / probability_discovery
            total_temp_power_consumed = 0
            total_temp_duration = 0
            # power consumed and duration for listening state
            for i in range(int(number_of_listening_cycles)):
                temp_power_consumption, temp_duration = self.wifi_consumption_model_rx(True, self.probe_request_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_response_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                N = random.randint(1,3)
                total_temp_power_consumed = total_temp_power_consumed * N
                total_temp_duration += 0.1024 * N

            total_power_consumed += total_temp_power_consumed * 0.1024
            total_duration += total_temp_duration

            # power consumed and duration for search state
            # we assume number of search cycles to be equal to listening cycles
            # TODO: check if this is correct
            total_temp_power_consumed = 0
            total_temp_duration = 0
            for i in range(int(number_of_listening_cycles)):
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_request_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_response_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                # dwell time is 120 ms as per ESP32. Multiply by 3 doe 3 social channels
                total_temp_duration += self.dwell_time * 3
                total_temp_power_consumed *= self.dwell_time * 3

            # Total for device discovery as per Usman et al. paper
            total_power_consumed += total_temp_power_consumed
            total_duration += total_temp_duration

            # Association consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.association_request_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration

            # Group Owner Negotiation consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.group_owner_negotiation_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration

            # Group Formation consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.group_formation_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration
        else:
            # if not group owner
            # total energy consumption of the device in the discovery phase
            # we assume the probability of discovering the UE in a given cycle is 1/3
            probability_discovery = 1 / 3
            # the number of listening cycles then is 1/p
            number_of_listening_cycles = 1 / probability_discovery
            total_temp_power_consumed = 0
            total_temp_duration = 0
            # power consumed and duration for listening state
            for i in range(int(number_of_listening_cycles)):
                temp_power_consumption, temp_duration = self.wifi_consumption_model_rx(True, self.probe_request_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_response_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                N = random.randint(1, 3)
                total_temp_power_consumed = total_temp_power_consumed * N
                total_temp_duration += 0.1024 * N

            total_power_consumed += total_temp_power_consumed * 0.1024
            total_duration += total_temp_duration

            # power consumed and duration for search state
            # we assume number of search cycles to be equal to listening cycles
            # TODO: check if this is correct
            total_temp_power_consumed = 0
            total_temp_duration = 0
            for i in range(int(number_of_listening_cycles)):
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_request_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                temp_power_consumption, temp_duration = self.wifi_consumption_model_tx(True, self.probe_response_size)
                total_temp_power_consumed += temp_power_consumption
                total_temp_duration += temp_duration
                # dwell time is 120 ms as per ESP32. Multiply by 3 doe 3 social channels
                total_temp_duration += self.dwell_time * 3
                total_temp_power_consumed *= self.dwell_time * 3

            # Total for device discovery as per Usman et al. paper
            total_power_consumed += total_temp_power_consumed
            total_duration += total_temp_duration

            # Association consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_rx(True, self.association_response_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration

            # Group Owner Negotiation consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_rx(True, self.group_owner_negotiation_response_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration

            # Group Formation consumption
            temp_power_consumption, temp_duration = self.wifi_consumption_model_rx(True, self.group_formation_response_size)
            total_power_consumed += temp_power_consumption
            total_duration += temp_duration

        return total_power_consumed, total_duration

    def wifi_consumption_model_tx(self, man_or_data, payload_size):
        """
        WiFi energy consumption and time model for transmission
        :param payload_size:  (bytes) payload size of the frame
        :param man_or_data: (bool) management frame transmission or data frame transmission. True for management, False for data
        :return:  (W) energy consumption per frame and (s) total duration of frame transmission
        """

        if man_or_data:
            frame_transmit_time = (
                    (
                            payload_size)
                    * 8 / self.transmission_rate)  # (s) time to transmit frame of size L using MCS, T_L

            airtime_per_tx = frame_transmit_time  # (s) tx channel airtime percentage \tau_tx

            # (mW) energy consumption per frame
            total_power_consumed = (self.idle_consumption + self.tx_consumption * airtime_per_tx
                                    + self.cross_factor)
        else:
            frame_transmit_time = (
                    (
                            self.mac_preamble_size + self.plcp_header_size + self.udp_header_size + self.ip_header_size + payload_size)
                    * 8 / self.transmission_rate)  # (s) time to transmit frame of size L using MCS, T_L

            airtime_per_tx = frame_transmit_time  # (s) tx channel airtime percentage \tau_tx

            # (mW) energy consumption per frame
            total_power_consumed = (self.idle_consumption + self.tx_consumption * airtime_per_tx
                                    + self.cross_factor)

        # convert to Watt
        total_power_consumed = total_power_consumed / 1000

        total_duration = airtime_per_tx + frame_transmit_time  # (s) total duration of frame transmission

        return total_power_consumed, total_duration

    def wifi_consumption_model_rx(self, man_or_data, payload_size):
        """
        WiFi energy consumption and time model for reception
        :param payload_size:  (bytes) payload size of the frame
        :param man_or_data: (bool) management frame reception or data frame reception. True for management, False for data
        :return:  (W) energy consumption per frame and (s) total duration of frame reception
        """
        if man_or_data:
            frame_transmit_time = (
                    (
                            payload_size)
                    * 8 / self.transmission_rate)  # (s) time to transmit frame of size L using MCS, T_L

            airtime_per_rx = frame_transmit_time  # (s) rx channel airtime percentage \tau_rx

            # (mW) energy consumption per frame
            total_power_consumed = (self.idle_consumption + self.rx_consumption * airtime_per_rx
                                    + self.cross_factor_rx)

        else:
            frame_transmit_time = (
                    (
                            self.mac_preamble_size + self.plcp_header_size + self.udp_header_size + self.ip_header_size + payload_size)
                    * 8 / self.transmission_rate)  # (s) time to transmit frame of size L using MCS, T_L

            airtime_per_rx = frame_transmit_time  # (s) rx channel airtime percentage \tau_rx

            # (mW) energy consumption per frame
            total_power_consumed = (self.idle_consumption + self.rx_consumption * airtime_per_rx
                                    + self.cross_factor_rx)

        # convert to Watt
        total_power_consumed = total_power_consumed / 1000

        total_duration = airtime_per_rx + frame_transmit_time  # (s) total duration of frame reception

        return total_power_consumed, total_duration
