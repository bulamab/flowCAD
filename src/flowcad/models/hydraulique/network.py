
from .links import *
from .nodes import *
from ..fluid import Fluid  

from wntr.sim.results import SimulationResults

class HydraulicNetwork:
    """
    Classe représentant un réseau hydraulique composé de nœuds et de liens.
    """
    def __init__(self, fluid: Fluid = Fluid()):
        self.nodes = {}
        self.links = {}
        self.fluid = fluid  # Propriétés du fluide utilisé dans le réseau

    def add_node(self, node: HydraulicNode):
        if node.id in self.nodes:
            raise ValueError(f"Nœud avec ID '{node.id}' existe déjà dans le réseau.")
        self.nodes[node.id] = node

    def add_link(self, link: HydraulicLink):
        if link.id in self.links:
            raise ValueError(f"Lien avec ID '{link.id}' existe déjà dans le réseau.")
        if link.start_node not in self.nodes or link.end_node not in self.nodes:
            raise ValueError("Les nœuds de début et de fin du lien doivent exister dans le réseau.")
        self.links[link.id] = link

    def validate_flowcad(self):
        errors = []
        for node in self.nodes.values():
            node_errors = node.validate_flowcad()
            if node_errors:
                errors.append(f"Erreurs dans le nœud '{node.id}': " + "; ".join(node_errors))
        
        for link in self.links.values():
            link_errors = link.validate_flowcad()
            if link_errors:
                errors.append(f"Erreurs dans le lien '{link.id}': " + "; ".join(link_errors))
        
        return errors

    def to_wntr(self):
        import wntr
        wn_network = wntr.network.WaterNetworkModel()

        #definir les propriétés du fluide dans le modèle WNTR, pour le cas ou le fluide n'est pas de l'eau
        wn_network.options.hydraulic.viscosity = self.fluid.relative_viscosity()
        wn_network.options.hydraulic.specific_gravity = self.fluid.relative_density()
        
        # Ajouter les nœuds
        for node in self.nodes.values():
            node.to_wntr(wn_network)
        
        # Ajouter les liens
        for link in self.links.values():
            link.to_wntr(wn_network)
        
        return wn_network
    
    #cherche les résultats de la simulation dans la couche wntr et les attribue aux composants
    def get_results_from_wntr(self, wntr_results: SimulationResults):
        for node in self.nodes.values():
            node.get_results_from_wntr(wntr_results)
        
        for link in self.links.values():
            link.get_results_from_wntr(wntr_results)
    
    #Représentation textuelle du réseau hydraulique
    def __str__(self) -> str:   
        node_str = "\n".join(str(node) for node in self.nodes.values())
        link_str = "\n".join(str(link) for link in self.links.values())
        return f"HydraulicNetwork(fluid={self.fluid})\nNodes:\n{node_str}\nLinks:\n{link_str}"
    
#Test simple de la classe HydraulicNetwork
if __name__ == "__main__":
    # Créer un réseau
    network = HydraulicNetwork()
    
    # Ajouter des nœuds
    #j1 = Junction("J1", demand=0.0, elevation=10.0)
    r1 = Reservoir("R1", head=50.0, elevation=10.0)
    r2 = Reservoir("R2", head=50.0, elevation=0.0)
    network.add_node(r1)
    network.add_node(r2)
    
    # Ajouter un lien
    p1 = Pipe("P1", start_node="R1", end_node="R2", length=100, diameter=0.3, roughness=100)
    network.add_link(p1)
    
    print(network)
    print("Validation réseau:", network.validate_flowcad())
    
    # Convertir en modèle WNTR
    wntr_network = network.to_wntr()
    print("Modèle WNTR créé avec succès.")
    
    # Afficher les nœuds et liens WNTR
    print("Nœuds WNTR:", wntr_network.node_name_list)
    print("Liens WNTR:", wntr_network.link_name_list)