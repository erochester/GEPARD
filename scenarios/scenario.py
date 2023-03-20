from scenarios.shopping_mall import ShoppingMall
from scenarios.hospital import Hospital


class Scenario:
    def __init__(self, scenario, list_of_users, iot_device):
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        if scenario == "shoppingmall":
            self.scenario = ShoppingMall(list_of_users, iot_device)
        elif scenario == "hospital":
            self.scenario = Hospital(list_of_users, iot_device)

    def generate_scenario(self):
        return self.scenario.generate_scenario()

    def plot_scenario(self):
        return self.scenario.plot_scenario()
