from scenarios.shopping_mall import ShoppingMall
from scenarios.hospital import Hospital
from scenarios.university import University
import sys


class Scenario:
    def __init__(self, scenario, list_of_users, iot_device):
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        if scenario == "shopping_mall":
            self.scenario = ShoppingMall(list_of_users, iot_device)
        elif scenario == "hospital":
            self.scenario = Hospital(list_of_users, iot_device)
        elif scenario == "university":
            self.scenario = University(list_of_users, iot_device)
        else:
            print("Scenario not supported")
            sys.exit(1)

    def generate_scenario(self, distribution):
        return self.scenario.generate_scenario(distribution)

    def plot_scenario(self):
        return self.scenario.plot_scenario()
