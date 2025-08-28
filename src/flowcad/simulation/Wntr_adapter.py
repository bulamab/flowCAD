from ..models.hydraulique.network import HydraulicNetwork
from ..models.hydraulique.components import HydraulicComponent, HydraulicNode, HydraulicLink
from ..models.hydraulique.nodes import Junction, Reservoir, tank
from ..models.hydraulique.links import Pipe, Pump, Valve   
from typing import List 

import wntr 

class SimulationManager:
    """
    Classe pour gérer la simulation hydraulique en utilisant WNTR.
    
    Cette classe encapsule la création du réseau hydraulique, 
    l'ajout de composants, la validation et l'exécution de la simulation.
    """
    
    def __init__(self):
        self.network = HydraulicNetwork()
    
    def add_node(self, node: HydraulicNode):
        self.network.add_node(node)
    
    def add_link(self, link: HydraulicLink):
        self.network.add_link(link)
    
    def validate(self) -> List[str]:
        return self.network.validate_flowcad()
    
    def run_simulation(self):
        wn_network = self.network.to_wntr()
        
        #paramétrer les options de simulation   
        wn_network.options.time.duration = 3600  # 1 heure
        wn_network.options.time.hydraulic_timestep = 3600  # Pas de 1 heure
        wn_network.options.time.report_timestep = 3600  # Configurer le pas de rapport
        wn_network.options.hydraulic.headloss = 'D-W'  # Utiliser la formule de Darcy-Weisbach  


        # Configurer la simulation
        sim = wntr.sim.EpanetSimulator(wn_network)
        
        # Exécuter la simulation
        results = sim.run_sim()
        
        return results

# Test simple de la classe SimulationManager
if __name__ == "__main__":
    sim_manager = SimulationManager()  # Créer le gestionnaire de simulation

    #ajouter deux réservoirs
    r1 = Reservoir("R1", head=10.0)
    r2 = Reservoir("R2", head=40.0)
    sim_manager.add_node(r1) # Ajouter le réservoir au réseau
    sim_manager.add_node(r2) # Ajouter le réservoir au réseau

    #ajouter une jonction intermédiaire
    j1 = Junction("J1", demand=0.0, elevation=0.0)
    j2 = Junction("J2", demand=0.0, elevation=0.0)
    sim_manager.add_node(j2) # Ajouter la jonction au réseau
    sim_manager.add_node(j1) # Ajouter la jonction au réseau

    # Ajouter un tuyau entre R1 et J1
    p1 = Pipe("P1", start_node="R1", end_node="J1", length=100.0, diameter=0.3, roughness=0.0002)
    sim_manager.add_link(p1)  # Ajouter le tuyau au réseau 
    ## Ajouter un tuyau entre J1 et R2
    #p2 = Pipe("P2", start_node="J1", end_node="R2", length=100.0, diameter=0.3, roughness=0.0002)
    #sim_manager.add_link(p2)  # Ajouter le tuyau au réseau

    #Ajouter une pompe entre J2 et R2
    p2 = Pump("P2", start_node="J2", end_node="R2", curve_points=[(1, 30)]) # 
    sim_manager.add_link(p2)  # Ajouter la pompe au réseau

    #ajouter une valve entre J1 et J2
    v1 = Valve("V1", start_node="J1", end_node="J2", diameter=0.2, valve_type='PRV', setting=20.0)
    sim_manager.add_link(v1)  # Ajouter la valve au réseau

    # Valider le réseau
    errors = sim_manager.validate()
    if errors:
        print("Erreurs de validation:")
        for error in errors:
            print(f" - {error}") 
    else:
        print("Réseau validé avec succès.")
        
        # Exécuter la simulation
        results = sim_manager.run_simulation()
        
        # Afficher les résultats
        print("Pressions aux nœuds:")
        for node_id in ["R1", "J1", "R2"]:
            pressure = results.node['pressure'].loc[0, node_id]
            print(f"  {node_id}: {pressure:.2f} m")
        
        print("Charge totale aux nœuds:")
        for node_id in ["R1", "J1", "J2", "R2"]:
            head = results.node['head'].loc[0, node_id]
            print(f"  {node_id}: {head:.2f} m")
        
        print("Débits dans les tuyaux/pompes/vannes:")
        print(f"  P1: {results.link['flowrate'].loc[0, 'P1']*1000:.2f} L/s")
        print(f"  P2: {results.link['flowrate'].loc[0, 'P2']*1000:.2f} L/s")
        print(f"  V1: {results.link['flowrate'].loc[0, 'V1']*1000:.2f} L/s")