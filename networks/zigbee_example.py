from networks.zigbee import ZigBee
import matplotlib.pyplot as plt

zigbee = ZigBee()
# We test against the mean drain current (mA) as published in the reference papers (E. Casilari et al.)

payload = 102  # bytes

# We calculate the mean drain current (mA)

t_tx = (8 * (31 + payload)) / 250000  # s, where 250000 is the data rate in bps

i_tx = 0.0305  # A

t_onoff = 0.013  # s is the wake-up and turn off the transceiver and transmit data to MCU time

i_onoff = 0.013  # A

t_list = 0.0029  # s is the time to tune required to access the radio channel (CSMA/CA) and receive the ACK

i_list = 0.0325  # A

i_sleep = 0.00000075  # A

total_duration = t_tx + t_onoff + t_list

i_drain_results = []

for t in range(1, 17):
    i_drain = ((total_duration) / t) * (((t_onoff * i_onoff) + (t_list * i_list) + (t_tx * i_tx)) / total_duration) + (
                1 - (total_duration) / t) * i_sleep
    i_drain_results.append(i_drain)

# convert results to mA
i_drain_results = [i * 1000 for i in i_drain_results]

# plot the results against t

plt.plot(range(1, 17), i_drain_results, label="Calculated results", marker='o')
# add results from the paper
plt.plot([1, 2, 4, 6, 8, 10, 12, 14, 16], [0.4, 0.21, 0.1, 0.06, 0.05, 0.04, 0.03, 0.029, 0.028],
         label="Reference results", marker='x')
plt.xlabel("Time between consecutive transmissions (s)")
plt.ylabel("Drain current (mA)")

# show legend
plt.legend()
plt.show()

# Note: any difference between the calculated and reference results is due to the fact that the reference results are
# not given, and we have to estimate them from the graph in the paper.
