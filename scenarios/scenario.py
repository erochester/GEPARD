from scenarios.shopping_mall import ShoppingMall
from scenarios.hospital import Hospital
from scenarios.university import University
from scenarios.example_scenario import ExampleScenario
import sys
import logging

class Scenario:
    """
    Metaclass for the Scenarios. Used to unify and call different scenario implementations.
    """
    def __init__(self, scenario, list_of_users, iot_device, network):
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        if scenario == "example_scenario":
            self.scenario = ExampleScenario(list_of_users, iot_device, network)
        elif scenario == "shopping_mall":
            self.scenario = ShoppingMall(list_of_users, iot_device, network)
        elif scenario == "hospital":
            self.scenario = Hospital(list_of_users, iot_device, network)
        elif scenario == "university":
            self.scenario = University(list_of_users, iot_device, network)
        else:
            logging.error("Scenario not supported")
            sys.exit(1)

    def generate_scenario(self, distribution):
        """
        Generates the scenario objects and populates them, e.g., users.
        :param distribution: Distribution to use for user arrival/departure processes.
        :return:
        """
        return self.scenario.generate_scenario(distribution)

    def plot_scenario(self):
        """
        Method used to vizualize the scenario, i.e., space, user arrival/departure points and
        trajectory across the space.
        """
        return self.scenario.plot_scenario()
