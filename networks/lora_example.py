import math

"""
Showcasing an example usage for LoRa. The results are used to validate the implementation by comparing the results
with existing LoRa airtime and power consumption calculators.
"""

payload = 217

# How many packets to send
packet_num = math.ceil(payload / 51)

t_tx = 0
t_sym = (2 ** 10) / 250
t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
# does the payload fit into 1 packet?
if packet_num > 1:
    while payload - 51 > 0:
        payload = payload - 51
        n_phy = 8 + max(math.ceil((28 + 8 * (payload) + 4 * 10) /
                                  (4 * 10)) * (4/5 + 4), 0)
        t_phy = t_sym * n_phy
        t_temp_tx = t_pre + t_phy
        t_tx = t_temp_tx

n_phy = 8 + max(math.ceil((28 + 8 * payload + 4 * 10) /
                          (4 * 10)) * (4/5 + 4), 0)
t_phy = t_sym * n_phy
t_temp_tx = t_pre + t_phy
t_tx += t_temp_tx

print((t_tx / 3600) * 3.3 * (125 / 1000), t_tx)