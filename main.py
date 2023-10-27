import argparse
import logging
import random
import xml.etree.ElementTree as ET
import numpy as np

from driver import Driver
from iot_device import IoTDevice
from negotiation_protocols.negotiation import NegotiationProtocol
from networks.network import Network
from scenarios.scenario import Scenario
from util import result_file_util, write_results
from process_results import ResultProcessor


def main(scenario_name, network_type, device_type_list, algo, filename):

    # make scenario lower case for consistency
    scenario_name = scenario_name.lower()

    # same for the network type
    network_type = network_type.lower()

    # same for the device type
    device_type= device_type_list[0].lower()
    device_type = device_type_list[1].lower()

    # same for the algorithm
    algo = algo.lower()

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
    network = Network(network_type, device_type, logger)

    # create the negotiation protocol object that determines the rules of the encounter
    negotiation_protocol = NegotiationProtocol(algo, network, logger)

    driver = Driver(scenario, network, negotiation_protocol, logger)

    total_consented, total_user_power_consumption, total_owner_power_consumption, \
        total_user_time_spent, total_owner_time_spent, end_time, list_of_users, iot_device \
        = driver.run()  # drives the simulation environment

    # Find the maximum utility
    max_utility = max([u.utility for u in list_of_users])

    # Find the minimum utility
    min_utility = min([u.utility for u in list_of_users])

    # Scaling utilites
    for u in list_of_users:
        u.utility = (u.utility - min_utility) / (max_utility - min_utility) * 100

    # Scale iot device utility
    iot_device.utility = ((iot_device.utility - min_utility) / (max_utility - min_utility) * 100)/len(list_of_users)

    # Write to csv
    # Define the data rows
    rows = [[algo, network_type, scenario_name, round(total_user_power_consumption, 2),
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

    msg = "GEPARD environment. Please provide -a, -d and -n arguments to setup algorithm, device and network type."
    # Initialize parser
    parser = argparse.ArgumentParser(description=msg)

    filename = "./results/results.csv"
    result_file_util(filename)

    # Adding optional argument
    parser.add_argument("-a", "--algo", help="Algorithm to use, e.g., alanezi")
    parser.add_argument("-n", "--network", help="Network protocol to use, e.g., ble")
    parser.add_argument('-d', '--devices', nargs='+', help="List of specific devices to use, e.g., esp32")
    parser.add_argument("-s", "--scenario", help="Scenario to use, e.g., shopping_mall")
    parser.add_argument("-t", "--tournament", help="Tournament-styled testing", action='store_true')

    # Read arguments from command line
    args = parser.parse_args()

    # default seed for reproducibility
    random.seed(123)

    if args.tournament:
        # Load the XML file
        tree = ET.parse('tournament_setup.xml')
        root = tree.getroot()
        runs = int(root.find('runs').text)
        networks = [network.text for network in root.findall('networks/network')]
        devices = [device.text for device in root.findall('devices/device')]
        scenarios = [scenario.text for scenario in root.findall('scenarios/scenario')]
        algorithms = [algorithm.text for algorithm in root.findall('algorithms/algorithm')]
        # Run the code for each combination of algorithm, network, and scenario
        for algorithm in algorithms:
            for network in networks:
                for scenario in scenarios:
                    for i in range(runs):
                        # use run number for seed
                        random.seed(i + 1)
                        # Run your code here with the current combination of algorithm, network, and scenario
                        print(f"Run {i + 1} of {runs} for algorithm {algorithm}, network {network}, "
                              f"and scenario {scenario}")
                        main(scenario, network, algorithm, filename)
    else:
        if not args.algo or not args.network or not args.scenario:
            parser.error("[!] Please provide -a, -s and -n arguments to setup algorithm, scenario and network type.")
            exit(1)
        algo = args.algo
        print("[!] Algorithm: ", algo)
        network_type = args.network
        print("[!] Network: ", network_type)
        scenario_name = args.scenario
        print("[!] Scenario: ", scenario_name)

        main(scenario_name, network_type, algo, filename)

    # Process results
    result_processor = ResultProcessor()
    result_processor.process_results()
    result_processor.plot_results()



