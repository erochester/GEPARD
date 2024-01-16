import matplotlib.pyplot as plt

"""
Read the file line by line:
 - for each line, split it using whitespace
 - first element is the user id and the second is the number of phases
 - store the largest number of phases in the list
"""

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
