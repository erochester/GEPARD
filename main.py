import argparse
import logging
from logging_module import setup_logging
import random
from xml.etree.ElementTree import parse
import os

import numpy as np

from driver import Driver
from iot_device import IoTDevice
from negotiation_protocols.negotiation import NegotiationProtocol
from networks.network import Network
from process_results import ResultProcessor
from scenarios.scenario import Scenario
from util import result_file_util, write_results, Distribution, calc_norm_utility


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

    # network technology that determines the range of communication, power consumed and allowed data rates
    network = Network(network_type)

    # Generates the users/PAs
    scenario = Scenario(scenario_name, list_of_users, iot_device, network)
    scenario.generate_scenario(dist)
    logging.debug("Number of users: %s", len(scenario.list_of_users))

    # plot user locations
    # uncomment if you want to plot the IoT area with user arrival/departure locations and trajectories
    # scenario.plot_scenario()

    # create the negotiation protocol object that determines the rules of the encounter
    negotiation_protocol = NegotiationProtocol(protocol, network)

    driver = Driver(scenario, negotiation_protocol)

    total_consented, total_user_power_consumption, total_owner_power_consumption, \
        total_user_time_spent, total_owner_time_spent, end_time, list_of_users, iot_device \
        = driver.run()  # drives the simulation environment

    # calculate normalized utilities
    calc_norm_utility(list_of_users, 0)
    calc_norm_utility(list_of_users+[iot_device], 1)

    # Write to csv
    # Define the data rows
    rows = [[protocol, network_type, scenario_name, round(total_user_power_consumption, 2),
             round(total_owner_power_consumption, 2), round(total_user_time_spent, 2), round(total_owner_time_spent, 2),
             total_consented, len(list_of_users), round((total_consented / len(list_of_users)) * 100, 2),
             round(end_time, 2), round(np.mean([u.utility for u in list_of_users]), 2), round(iot_device.utility, 2),
             round(np.mean([u.norm_utility for u in list_of_users]), 2), round(iot_device.norm_utility, 2)]]

    write_results(filename, rows)


if __name__ == "__main__":

    msg = "GEPARD environment. Please provide -p, -s and -n arguments to setup protocol, scenario and network type."
    # Initialize parser
    parser = argparse.ArgumentParser(description=msg)

    # Adding optional argument
    parser.add_argument("-p", "--protocol", help="Negotiation protocol to use, e.g., alanezi")
    parser.add_argument("-n", "--network", help="Network protocol to use, e.g., ble")
    parser.add_argument("-s", "--scenario", help="Scenario to use, e.g., shopping_mall")
    parser.add_argument("-t", "--tournament", help="Tournament-styled testing", action='store_true')
    parser.add_argument("-d", "--distribution", help="Distribution to use, e.g., poisson")
    parser.add_argument("-v", "--verbose", help="Enable verbose output", action="store_true")

    # Read arguments from command line
    args = parser.parse_args()

    # Set up logging
    setup_logging(verbose=args.verbose)

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the results file relative to the script directory
    file_path = os.path.join(script_dir, 'results/results.csv')

    result_file_util(file_path)

    if not args.distribution:
        distribution_type = "poisson"
    else:
        distribution_type = args.distribution

    # default seed for reproducibility
    random.seed(123)
    np.random.seed(123)

    if args.tournament:

        # Construct the path to the XML file relative to the script directory
        xml_file_path = os.path.join(script_dir, 'tournament_setup.xml')

        # Load the XML file
        tree = parse(xml_file_path)
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
                        logging.info(f"Run {i + 1} of {runs} for protocol {protocol}, network {network}, "
                              f"and scenario {scenario}")
                        main(scenario, network, protocol, file_path, distribution_type)
    else:
        if not args.protocol or not args.network or not args.scenario:
            parser.error("Please provide -a, -s and -n arguments to setup protocol, scenario and network type.")
            exit(1)
        protocol = args.protocol
        logging.info("Protocol: %s", protocol)
        network_type = args.network
        logging.info("Network: %s", network_type)
        scenario_name = args.scenario
        logging.info("Scenario: %s", scenario_name)
        main(scenario_name, network_type, protocol, file_path, distribution_type)

    logging.info("Processing Results!")
    # Process results
    result_processor = ResultProcessor()
    result_processor.process_results(script_dir)
    # Plot results only works for tournament for now
    result_processor.plot_results(script_dir)
