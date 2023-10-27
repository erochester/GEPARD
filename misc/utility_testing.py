import random

import matplotlib.pyplot as plt
#
# users = 100
# d = []
# f = []
# g = []
# for u in range(0,users):
#     privacy_coeff = random.choice([1] * 25 + [2] * 55 + [3] * 20)
#     consent = False
#     d.append(u)
#     f.append(privacy_coeff)
#     if privacy_coeff == 1:
#         if random.randint(1,100) <= 20.4:
#             consent = True
#     elif privacy_coeff == 2:
#         if random.randint(1,100) <= 73.55:
#             consent = True
#     else:
#         consent = True
#     g.append(consent)
#
# z = []
# x = []
# y = []
# for u in range(0,users):
#     privacy_coeff = random.choice([1] * 25 + [2] * 55 + [3] * 20)
#     z.append(u)
#     x.append(privacy_coeff)
#     consent = False
#     if privacy_coeff == 1:
#         gamma = 1
#         p = 3*2*1*1
#         b = 3+2+1+1
#         u = -gamma*p+b
#         if u >= 0:
#             consent = True
#     elif privacy_coeff == 2:
#         gamma = 0.5
#         p = 3*2*1*1
#         b = 3+2+1+1
#         u = -gamma*p+b
#         if u >= 0:
#             consent = True
#     else:
#         gamma = 0
#         p = 3*2*1*1
#         b = 3+2+1+1
#         u = -gamma*p+b
#         if u >= 0:
#             consent = True
#     print(u, " ", gamma, " ", p, " ", b)
#     y.append(consent)
#
#
# fig, axs = plt.subplots(2)
# axs[0].scatter(z, y)
#
# for i, label in enumerate(x):
#     axs[0].annotate(label, (z[i], y[i]))
#
# axs[1].scatter(d, g)
#
# for i, label in enumerate(f):
#     axs[1].annotate(label, (d[i], g[i]))
#
# plt.show()

# read the file line by line
# for each line, split it using whitespace
# first element is the user id and the second is the number of phases
# store the largest number of phases in the list
file = open('./user_consent_phase.txt', 'r')
lines = file.readlines()

phases = {}

for line in lines:
    # check if exists in the dictionary
    if int(line.split()[0]) in phases:
        # check if it is larger than the current value
        if phases[int(line.split()[0])] < int(line.split()[1]):
            phases[int(line.split()[0])] = int(line.split()[1])
    else:
        phases[int(line.split()[0])] = int(line.split()[1])

# count the number of users for each phase
phase_count = {}
for key, value in phases.items():
    if value in phase_count:
        phase_count[value] += 1
    else:
        phase_count[value] = 1

# show gridlines
plt.grid(True)

# make gridlines dashed
plt.grid(linestyle='--')

# make gridlines be behind the plot elements
plt.gca().set_axisbelow(True)


# plot the number of users for each phase
plt.bar(phase_count.keys(), phase_count.values(), color='b')

# leave only phase numbers on the x-axis
plt.xticks(list(phase_count.keys()))

plt.xlabel('Number of Phases')
plt.ylabel('Number of Users')

# save the plot
plt.savefig('user_consent_phase.pdf')

