from negotiation_protocols.cunche import Cunche
from negotiation_protocols.alanezi import Alanezi
from negotiation_protocols.concession import Concession


class NegotiationProtocol:
    def __init__(self, algo, network, logger):
        self.algo = algo
        self.network = network
        self.logger = logger

    def run(self, list_of_users, iot_device):
        if self.algo == "alanezi":
            alanezi = Alanezi(self.network)
            return alanezi.run(list_of_users, iot_device)
        elif self.algo == "cunche":
            cunche = Cunche(self.network)
            return cunche.run(list_of_users, iot_device)
        elif self.algo == "concession":
            concession = Concession(self.network)
            return concession.run(list_of_users, iot_device)

