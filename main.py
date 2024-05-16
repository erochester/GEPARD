import argparse
import logging
import random
from xml.etree.ElementTree import parse

import numpy as np

from driver import Driver
from iot_device import IoTDevice
from negotiation_protocols.negotiation import NegotiationProtocol
from networks.network import Network
from process_results import ResultProcessor
from scenarios.scenario import Scenario
from util import result_file_util, write_results, Distribution


def main(scenario_name, network_type, protocol, filename, distribution_type):
    # make scenario lower case for consistency
    scenario_name = scenario_name.lower()

    # same for the network type
    network_type = network_type.lower()

    # same for the protocol
    protocol = protocol.lower()

    # create the scenario that determines user types, locations and movement patterns, network parameters and
    # simulation runtime
    list_of_users = []

    # initialize iot device
    # We assume that the IoT device is always at the center of the environment, i.e., (0,0).
    iot_device = IoTDevice((0, 0))

    # create distribution object
    dist = Distribution(distribution_type)

    # Generates the users/PAs
    scenario = Scenario(scenario_name, list_of_users, iot_device)
    scenario.generate_scenario(dist)
    print("Number of users: ", len(scenario.list_of_users))

    # plot user locations
    # uncomment if you want to plot the IoT area with user arrival/departure locations and trajectories
    # scenario.plot_scenario()

    # network technology that determines the range of communication, power consumed and allowed data rates
    network = Network(network_type, logger)

    # create the negotiation protocol object that determines the rules of the encounter
    negotiation_protocol = NegotiationProtocol(protocol, network, logger)

    driver = Driver(scenario, negotiation_protocol, logger)

    total_consented, total_user_power_consumption, total_owner_power_consumption, \
        total_user_time_spent, total_owner_time_spent, end_time, list_of_users, iot_device \
        = driver.run()  # drives the simulation environment

    # Find the maximum utility
    max_utility = max([u.utility for u in list_of_users])

    # Find the minimum utility
    min_utility = min([u.utility for u in list_of_users])

    # Scaling utilities
    for u in list_of_users:
        # check that utilities are non-zero
        if max_utility != 0:
            u.utility = (u.utility - min_utility) / (max_utility - min_utility) * 100

    # check that utilities are non-zero
    if max_utility != 0:
        # Scale iot device utility
        iot_device.utility = ((iot_device.utility - min_utility) / (max_utility - min_utility) * 100) / len(
            list_of_users)

    # Write to csv
    # Define the data rows
    rows = [[protocol, network_type, scenario_name, round(total_user_power_consumption, 2),
             round(total_owner_power_consumption, 2), round(total_user_time_spent, 2), round(total_owner_time_spent, 2),
             total_consented, len(list_of_users), round((total_consented / len(list_of_users)) * 100, 2),
             round(end_time, 2), round(np.mean([u.utility for u in list_of_users]), 2), round(iot_device.utility, 2)]]

    write_results(filename, rows)


if __name__ == "__main__":
    # Create and configure logger
    logging.basicConfig(filename="debug.log", format='%(asctime)s %(message)s', filemode='w')
    # Creating an object
    logger = logging.getLogger()

    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    msg = "GEPARD environment. Please provide -p, -s and -n arguments to setup protocol, scenario and network type."
    # Initialize parser
    parser = argparse.ArgumentParser(description=msg)

    filename = "./results/results.csv"
    result_file_util(filename)

    # Adding optional argument
    parser.add_argument("-p", "--protocol", help="Negotiation protocol to use, e.g., alanezi")
    parser.add_argument("-n", "--network", help="Network protocol to use, e.g., ble")
    parser.add_argument("-s", "--scenario", help="Scenario to use, e.g., shopping_mall")
    parser.add_argument("-t", "--tournament", help="Tournament-styled testing", action='store_true')
    parser.add_argument("-d", "--distribution", help="Distribution to use, e.g., poisson")

    # Read arguments from command line
    args = parser.parse_args()

    if not args.distribution:
        distribution_type = "poisson"
    else:
        distribution_type = args.distribution

    # default seed for reproducibility
    random.seed(123)

    if args.tournament:
        # Load the XML file
        tree = parse('tournament_setup.xml')
        root = tree.getroot()
        runs = int(root.find('runs').text)
        networks = [network.text for network in root.findall('networks/network')]
        scenarios = [scenario.text for scenario in root.findall('scenarios/scenario')]
        protocols = [protocol.text for protocol in root.findall('protocols/protocol')]
        # Run the code for each combination of protocol, network, and scenario
        for protocol in protocols:
            for network in networks:
                for scenario in scenarios:
                    for i in range(runs):
                        # use run number for seed
                        random.seed(i + 1)
                        # Run your code here with the current combination of protocol, network, and scenario
                        print(f"Run {i + 1} of {runs} for protocol {protocol}, network {network}, "
                              f"and scenario {scenario}")
                        main(scenario, network, protocol, filename, distribution_type)
    else:
        if not args.protocol or not args.network or not args.scenario:
            parser.error("[!] Please provide -a, -s and -n arguments to setup protocol, scenario and network type.")
            exit(1)
        protocol = args.protocol
        print("[!] Protocol: ", protocol)
        network_type = args.network
        print("[!] Network: ", network_type)
        scenario_name = args.scenario
        print("[!] Scenario: ", scenario_name)
        main(scenario_name, network_type, protocol, filename, distribution_type)

    print("Processing Results!")
    # Process results
    result_processor = ResultProcessor()
    result_processor.process_results()
    # Plot results only works for tournament for now
    result_processor.plot_results()
