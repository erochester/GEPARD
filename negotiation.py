from util import check_distance
import random
from cunche import Cunche
from alanezi import Alanezi


class NegotiationProtocol:
    def __init__(self, algo, network, logger):
        self.algo = algo
        self.network = network
        self.logger = logger

    def run(self, list_of_users):
        if self.algo == "alanezi":
            alanezi = Alanezi(self.network)
            return alanezi.run(list_of_users)
        elif self.algo == "cunche":
            cunche = Cunche(self.network)
            return cunche.run(list_of_users)

