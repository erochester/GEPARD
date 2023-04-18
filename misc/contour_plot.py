import matplotlib.pyplot as plt
import numpy as np
import math

x = [0, 0, 1, 1]
y = [0, 1, 0, 1]

fig, ax = plt.subplots()

ax.scatter(x, y, s=100, facecolors='none', edgecolors='b')
ax.plot([0, 1], [0, 1])

ax.set_xlabel("Video Recording")
ax.set_ylabel("Data Retention Period")
ax.set_title("Iso-utility curves")

ax.set_xticks([0, 1])
ax.set_xticklabels(['blurred', 'yes'])
ax.set_yticks([0, 1])
ax.set_yticklabels(['30-days', '1-year'])

plt.show()
