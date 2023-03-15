import argparse
import logging
import random
import csv
import os.path

from driver import Driver
from iot_device import IoTDevice
from negotiation import NegotiationProtocol
from network import Network
from scenario import Scenario


def main():
    random.seed(123)

    if not args.algo or not args.network:
        print("[!] Please provide -a and -n arguments to setup algorithm and network type.")
        exit(1)
    algo = args.algo
    print("[!] Algorithm: ", algo)
    network_type = args.network
    print("[!] Network: ", network_type)
    scenario_name = args.scenario
    print("[!] Scenario: ", scenario_name)

    # create the scenario that determines user types, locations and movement patterns, network parameters and
    # simulation runtime
    list_of_users = []

    # initialize iot device
    iot_device = IoTDevice((0, 0))

    # Generates the users/PAs
    scenario = Scenario(scenario_name, list_of_users, iot_device)
    scenario.generate_scenario()

    # plot user locations
    # scenario.plot_scenario()

    # network technology that determines the range of communication, power consumed and allowed data rates
    network = Network(network_type, logger)

    # create the negotiation protocol object that determines the rules of the encounter
    negotiation_protocol = NegotiationProtocol(algo, network, logger)

    driver = Driver(scenario, network, negotiation_protocol, logger)

    total_consented, total_user_power_consumption, total_owner_power_consumption, end_time = \
        driver.run()  # drives the simulation environment

    # Write to csv
    # Define the data rows
    rows = [[algo, network_type, scenario_name, round(total_user_power_consumption, 2),
             round(total_owner_power_consumption, 2),
             total_consented, len(list_of_users), round((total_consented / len(list_of_users)) * 100, 2),
             round(end_time, 2)]]

    # Open a file for writing
    filename = "results.csv"
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode) as csvfile:
        # Create a CSV writer object
        csvwriter = csv.writer(csvfile)

        # Write the column headers only if the file is newly created
        if mode == "w":
            fields = ["Algorithm", "Network", "Scenario", "Total User Power Consumption (kWh)",
                      "Total Owner Power Consumption (kWh)", "Consent collected from", "Total user number",
                      "Consent Percentage", "Total runtime (min)"]
            csvwriter.writerow(fields)

        # Write the data rows
        csvwriter.writerows(rows)


if __name__ == "__main__":
    # Create and configure logger
    logging.basicConfig(filename="debug.log", format='%(asctime)s %(message)s', filemode='w')
    # Creating an object
    logger = logging.getLogger()

    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    msg = "GEPARD environment. Please provide -a and -n arguments to setup algorithm and network type."
    # Initialize parser
    parser = argparse.ArgumentParser(description=msg)

    # Adding optional argument
    parser.add_argument("-a", "--algo", help="Algorithm to use, e.g., alanezi")
    parser.add_argument("-n", "--network", help="Network protocol to use, e.g., ble")
    parser.add_argument("-s", "--scenario", help="Scenario to use, e.g., shopping_mall")

    # Read arguments from command line
    args = parser.parse_args()

    main()
