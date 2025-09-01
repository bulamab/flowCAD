from typing import List 

from ..models.hydraulique.network import HydraulicNetwork
from ..models.hydraulique.components import HydraulicComponent, HydraulicNode, HydraulicLink
from ..models.hydraulique.nodes import Junction, Reservoir, tank
from ..models.hydraulique.links import Pipe, Pump, Valve   
from ..models.equipment.network_equipment import NetworkEquipment
from ..models.equipment.active_equipment import *
from ..models.equipment.connections import *


import wntr 

class SimulationManager:
    """
    Classe pour gérer la simulation hydraulique en utilisant WNTR.
    
    Cette classe encapsule la création du réseau hydraulique, 
    l'ajout de composants, la validation et l'exécution de la simulation.
    """
    
    def __init__(self, equipment_network: NetworkEquipment):
        self.equipment_network = equipment_network #réseau d'équipement
        self.hydraulic_network = equipment_network.to_hydraulic_network() #réseau hydraulique généré à partir du réseau d'équipement
    


    
    def run_simulation(self):
        wn_network = self.hydraulic_network.to_wntr()

        #afficher les propriétés du fluide utilisé
        print(f"  Viscosité: {wn_network.options.hydraulic.viscosity}")
        print(f"  Gravité spécifique: {wn_network.options.hydraulic.specific_gravity}")

        #paramétrer les options de simulation   
        wn_network.options.time.duration = 3600  # 1 heure
        wn_network.options.time.hydraulic_timestep = 3600  # Pas de 1 heure
        wn_network.options.time.report_timestep = 3600  # Configurer le pas de rapport
        wn_network.options.hydraulic.headloss = 'D-W'  # Utiliser la formule de Darcy-Weisbach  


        # Configurer la simulation
        sim = wntr.sim.EpanetSimulator(wn_network)
        
        # Exécuter la simulation
        results = sim.run_sim()

        print("Simulation terminée.")
        pressure = results.node['pressure']
        print("Pression (mCE)")
        print(pressure)
        print("Charge (mCE)")
        head = results.node['head']
        print(head)
        print("Débit (m³/s)")   
        flowrate = results.link['flowrate']
        print(flowrate)
        print("Vitesse (m/s)")
        velocity = results.link['velocity']
        print(velocity)
        print("Facteur de friction")
        friction_factor = results.link['friction_factor']
        print(friction_factor)
        print("Perte de charge (mCE/m)")
        headloss = results.link['headloss']
        print(headloss)

        #attribuer les résultats aux composants du réseau hydraulique
        self.hydraulic_network.get_results_from_wntr(results)

        #attribuer les résultats aux équipements du réseau d'équipement
        self.equipment_network.get_results_from_hydraulic_network(self.hydraulic_network)


        return results
    


# Test simple de la classe SimulationManager
if __name__ == "__main__":
    
    # Créer un réseau d'équipement
    network_eq = NetworkEquipment("Network1")

    """
    #-----------------------------------------------------------------------------------------
    #Test1: ecoulement entre 2 conditions aux limites de type pression
    #-----------------------------------------------------------------------------------------

    # Créer des équipements
    #pump_eq = PumpEquipment("Pump1", curve_points=[(50, 15), (100, 10)], elevation=5.0)
    pressure_High = PressureBoundaryConditionEquipment("PressureBC1", pressure_bar=3.0, elevation=10.0)
    pressure_Low = PressureBoundaryConditionEquipment("PressureBC2", pressure_bar=1.0, elevation=10.0)
    pipe_1 = PipeConnectionEquipment("Pipe1", length=100.0, diameter=0.15, roughness=0.2, elevation=10)
    pipe_2 = PipeConnectionEquipment("Pipe2", length=100.0, diameter=0.15, roughness=0.2, elevation=10)

    # Ajouter les équipements au réseau
    network_eq.add_equipment(pressure_High)
    network_eq.add_equipment(pressure_Low)
    network_eq.add_equipment(pipe_1)
    network_eq.add_equipment(pipe_2)


    # Connecter les équipements via leurs ports
    network_eq.connectEquipments(pressure_High, pressure_High.ports[f"{pressure_High.id}_P1"], pipe_1, pipe_1.ports[f"{pipe_1.id}_P1"])  # Connecter la sortie de la pompe à l'entrée du tuyau
    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P2"], pipe_2, pipe_2.ports[f"{pipe_2.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P2"], pressure_Low, pressure_Low.ports[f"{pressure_Low.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    """

    """
    #-----------------------------------------------------------------------------------------
    #Test2: ecoulement entre 1 condition aux limite type débit et 1 condition aux limites de type pression
    #-----------------------------------------------------------------------------------------
    
    # Créer des équipements
    #pump_eq = PumpEquipment("Pump1", curve_points=[(50, 15), (100, 10)], elevation=5.0)
    flowrate_bc = FlowRateBoundaryConditionEquipment("FlowrateBC1", flowrate_m3s=-0.01, elevation=10.0)
    pressure_Low = PressureBoundaryConditionEquipment("PressureBC2", pressure_bar=1.0, elevation=10.0)
    pipe_1 = PipeConnectionEquipment("Pipe1", length=100.0, diameter=0.15, roughness=0.2, elevation=10)
    pipe_2 = PipeConnectionEquipment("Pipe2", length=100.0, diameter=0.15, roughness=0.2, elevation=10)

    # Ajouter les équipements au réseau
    network_eq.add_equipment(flowrate_bc)
    network_eq.add_equipment(pressure_Low)
    network_eq.add_equipment(pipe_1)
    network_eq.add_equipment(pipe_2)


    # Connecter les équipements via leurs ports
    network_eq.connectEquipments(flowrate_bc, flowrate_bc.ports[f"{flowrate_bc.id}_P1"], pipe_1, pipe_1.ports[f"{pipe_1.id}_P1"])  # Connecter la sortie de la pompe à l'entrée du tuyau
    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P2"], pipe_2, pipe_2.ports[f"{pipe_2.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P2"], pressure_Low, pressure_Low.ports[f"{pressure_Low.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    """

    """
    #-----------------------------------------------------------------------------------------
    #Test3: ecoulement entre 1 condition aux limite type débit et 1 condition aux limites de type pression, avec une perte de charge singulière
    #-----------------------------------------------------------------------------------------
    
    # Créer des équipements
    #pump_eq = PumpEquipment("Pump1", curve_points=[(50, 15), (100, 10)], elevation=5.0)
    flowrate_bc = FlowRateBoundaryConditionEquipment("FlowrateBC1", flowrate_m3s=0.05, elevation=10.0)
    pressure_Low = PressureBoundaryConditionEquipment("PressureBC2", pressure_bar=1.0, elevation=10.0)
    HR_1 = HydraulicResistanceEquipment("HR_1", diameter=0.15, zeta=HydraulicConverter.zeta_from_kv(kv=1000, diameter=0.15))
    #HR_1 = HydraulicResistanceEquipment("HR_1", diameter=0.15, zeta=HydraulicConverter.zeta_from_nominal_conditions(flow_rate_m3s=0.05, head_loss_kPa=50, diameter=0.15))
    pipe_1 = PipeConnectionEquipment("Pipe1", length=100.0, diameter=0.15, roughness=0.2, elevation=10)
    pipe_2 = PipeConnectionEquipment("Pipe2", length=100.0, diameter=0.15, roughness=0.2, elevation=10)

    # Ajouter les équipements au réseau
    network_eq.add_equipment(flowrate_bc)
    network_eq.add_equipment(pressure_Low)
    network_eq.add_equipment(pipe_1)
    network_eq.add_equipment(pipe_2)
    network_eq.add_equipment(HR_1)


    # Connecter les équipements via leurs ports
    network_eq.connectEquipments(flowrate_bc, flowrate_bc.ports[f"{flowrate_bc.id}_P1"], pipe_1, pipe_1.ports[f"{pipe_1.id}_P1"])  # Connecter la sortie de la pompe à l'entrée du tuyau
    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P2"], HR_1, HR_1.ports[f"{HR_1.id}_P1"])  # Connecter la sortie du tuyau à la résistance hydraulique
    network_eq.connectEquipments(HR_1, HR_1.ports[f"{HR_1.id}_P2"], pipe_2, pipe_2.ports[f"{pipe_2.id}_P1"])  # Connecter la sortie de la résistance hydraulique au tuyau
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P2"], pressure_Low, pressure_Low.ports[f"{pressure_Low.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    """

    #-----------------------------------------------------------------------------------------
    #Test4: Réseau fermé, une source de débit, 2 Te, 2 tuyaux
    #-----------------------------------------------------------------------------------------
    
    # Créer des équipements
    #pump_eq = PumpEquipment("Pump1", curve_points=[(50, 15), (100, 10)], elevation=5.0)
    flowrate_bc = FlowRateBoundaryConditionEquipment("FlowrateBC1", flowrate_m3s=0.05, elevation=10.0)
    pressure_Low = PressureBoundaryConditionEquipment("PressureBC2", pressure_bar=1.0, elevation=10.0)
    
    pipe_1 = PipeConnectionEquipment("Pipe1", length=10.0, diameter=0.15, roughness=0.2, elevation=10)
    pipe_2 = PipeConnectionEquipment("Pipe2", length=100.0, diameter=0.15, roughness=0.2, elevation=10)

    Te1 = TeeConnectionEquipment("Te1", diameter=0.15, elevation=10)
    Te2 = TeeConnectionEquipment("Te2", diameter=0.15, elevation=10)

    # Ajouter les équipements au réseau
    network_eq.add_equipment(flowrate_bc)
    network_eq.add_equipment(pressure_Low)
    network_eq.add_equipment(pipe_1)
    network_eq.add_equipment(pipe_2)
    network_eq.add_equipment(Te1)
    network_eq.add_equipment(Te2)


    # Connecter les équipements via leurs ports
    network_eq.connectEquipments(flowrate_bc, flowrate_bc.ports[f"{flowrate_bc.id}_P1"], Te1, Te1.ports[f"{Te1.id}_P1"])  # Connecter la sortie de la BC au Te1

    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P1"], Te1, Te1.ports[f"{Te1.id}_P3"])  # Connecter le Te1 au Pipe 1
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P1"], Te1, Te1.ports[f"{Te1.id}_P2"])  # Connecter le Te1 au Pipe 2

    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P2"], Te2, Te2.ports[f"{Te2.id}_P1"])  # Connecter le Pipe 1 au Te2
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P2"], Te2, Te2.ports[f"{Te2.id}_P2"])  # Connecter le Pipe 2 au Te2
    
    network_eq.connectEquipments(Te2, Te2.ports[f"{Te2.id}_P3"], pressure_Low, pressure_Low.ports[f"{pressure_Low.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression

    print (f"Description du réseau d'équipements:\n {network_eq}")

    # Valider le réseau d'équipement
    print("Validation réseau d'équipement:", network_eq.validate_flowcad())

    print (f"Description du réseau hydraulique équivalent:\n {network_eq.to_hydraulic_network()}")



    #creer le gestionnaire de simulation
    sim_manager = SimulationManager(network_eq)

    results = sim_manager.run_simulation()

    print (f"Description du réseau d'équipements:\n {network_eq}")


    """print(results.node['pressure'])
    print(results.node['head'])
    print(results.link['flowrate'])
    print(results.link['velocity'])
    print(results.link['friction_factor'])
    print(results.link['headloss'])

    print(f"pression au noeud Pipe1_P2_to_Pipe2_P1: {results.node['pressure'].loc[0, 'Pipe1_P2_to_Pipe2_P1']} mCE")"""



    
