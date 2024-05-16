from negotiation_protocols.cunche import Cunche
from negotiation_protocols.alanezi import Alanezi
from negotiation_protocols.concession import Concession
import sys


class NegotiationProtocol:
    """
    Metaclass for Negotiation Protocols. Used to unify and call different negotiation protocols.
    """
    def __init__(self, protocol, network, logger):
        self.protocol = protocol
        self.network = network
        self.logger = logger

    def run(self, list_of_users, iot_device):
        """
        Driver for the negotiation protocols. Calls the respective negotiation protocol run().
        :param list_of_users: List of current users in the area (User object).
        :param iot_device: IoT device object.
        :return: Returns the calculated power and time consumption for users and IoT device.
        """
        if self.protocol == "alanezi":
            alanezi = Alanezi(self.network)
            return alanezi.run(list_of_users, iot_device)
        elif self.protocol == "cunche":
            cunche = Cunche(self.network)
            return cunche.run(list_of_users, iot_device)
        elif self.protocol == "concession":
            concession = Concession(self.network)
            return concession.run(list_of_users, iot_device)
        else:
            print("Negotiation protocol not supported")
            sys.exit(1)
