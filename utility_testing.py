from random import random
import matplotlib.pyplot as plt
import math
import random


users = 100
d = []
f = []
g = []
for u in range(0,users):
    privacy_coeff = random.choice([1] * 25 + [2] * 55 + [3] * 20)
    consent = False
    d.append(u)
    f.append(privacy_coeff)
    if privacy_coeff == 1:
        if random.randint(1,100) <= 20.4:
            consent = True
    elif privacy_coeff == 2:
        if random.randint(1,100) <= 73.55:
            consent = True
    else:
        consent = True
    g.append(consent)

z = []
x = []
y = []
for u in range(0,users):
    privacy_coeff = random.choice([1] * 25 + [2] * 55 + [3] * 20)
    z.append(u)
    x.append(privacy_coeff)
    consent = False
    if privacy_coeff == 1:
        gamma = 1
        p = 3*2*1*1
        b = 3+2+1+1
        u = -gamma*p+b
        if u >= 0:
            consent = True
    elif privacy_coeff == 2:
        gamma = 0.5
        p = 3*2*1*1
        b = 3+2+1+1
        u = -gamma*p+b
        if u >= 0:
            consent = True
    else:
        gamma = 0
        p = 3*2*1*1
        b = 3+2+1+1
        u = -gamma*p+b
        if u >= 0:
            consent = True
    print(u, " ", gamma, " ", p, " ", b)
    y.append(consent)


fig, axs = plt.subplots(2)
axs[0].scatter(z, y)

for i, label in enumerate(x):
    axs[0].annotate(label, (z[i], y[i]))

axs[1].scatter(d, g)

for i, label in enumerate(f):
    axs[1].annotate(label, (d[i], g[i]))

plt.show()