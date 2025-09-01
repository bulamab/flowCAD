#Definit les outils nécessaire pour faire un réseau d'équipement hydraulique
#Un équipement est un ensemble de composant hydraulique (noeud et lien) connectés entre eux
#Un équipement peut être un simple composant hydraulique (ex: une pompe) ou un  ensemble plus complexe (ex: une station de pompage avec réservoir, pompe, vanne, etc.)
from ..hydraulic_converter import *
from ..fluid import Fluid
from .base_equipment import *
from typing import List, Dict, Any, Optional
from .active_equipment import *
from .connections import *
from ..hydraulique.network import HydraulicNetwork
from ..hydraulique.components import HydraulicComponent 

class NetworkEquipment():
    def __init__(self, id: str):
        self.id = id
        self.equipments: List[BaseEquipment] = []
        self.connections: Dict[str, str] = {}
    
    #ajoute un équipement au réseau d'équipement-----------------------------------------------------------------------------
    def add_equipment(self, equipment: BaseEquipment):

        #ajoute un équipement au réseau d'équipement
        if equipment in self.equipments:
            raise ValueError(f"L'équipement '{equipment.id}' existe déjà dans le réseau.") 
        else:
            self.equipments.append(equipment)

    #connecte deux équipements via leurs ports respectifs (un des équipment peut être un tuyau)-----------------------------
    def connectEquipments(self, equipment1: BaseEquipment, port_equipment1: Port, equipment2: BaseEquipment, port_equipment2: Port):
        #connecte deux équipements via leurs ports respectifs (un des équipment peut être un tuyau))

        #vérifie que les équipements et ports existent
        if equipment1 not in self.equipments:
            raise ValueError(f"L'équipement '{equipment1.id}' n'existe pas dans le réseau.")
        if equipment2 not in self.equipments:
            raise ValueError(f"L'équipement '{equipment2.id}' n'existe pas dans le réseau.")
        if port_equipment1.id not in equipment1.ports:
            raise ValueError(f"Le port '{port_equipment1.id}' n'existe pas dans l'équipement '{equipment1.id}'.")
        if port_equipment2.id not in equipment2.ports:
            raise ValueError(f"Le port '{port_equipment2.id}' n'existe pas dans l'équipement '{equipment2.id}'.")

        #vérifie que les ports ne sont pas déjà connectés
        if port_equipment1.is_connected:
            raise ValueError(f"Le port '{port_equipment1.id}' de l'équipement '{equipment1.id}' est déjà connecté.")
        if port_equipment2.is_connected:
            raise ValueError(f"Le port '{port_equipment2.id}' de l'équipement '{equipment2.id}' est déjà connecté.")
        
        #connecter les ports
        port_equipment1.connect(equipment2.id, port_equipment2.id  ) #connecte le port 1 au port 2
        port_equipment2.connect(equipment1.id, port_equipment1.id  ) #connecte le port 2 au port 1

        #remplit le dictionnaire des connexions
        connection_name = f"{port_equipment1.id}_to_{port_equipment2.id}" #crée un nom unique pour la connexion
        self.connections[port_equipment1.id] = connection_name #associer le port connecté de l'équipment 1 à la connexion unique
        self.connections[port_equipment2.id] = connection_name #associer le port connecté de l'équipment 2 à la connexion unique

    #Validation simple du réseau d'équipement-----------------------------------------------------------------------------------
    def validate_flowcad(self) -> List[str]:
        errors = []
        #vérifie que tous les ports des équipements sont connectés
        for equipment in self.equipments:
            for port in equipment.ports.values():
                if not port.is_connected:
                    errors.append(f"Le port '{port.id}' de l'équipement '{equipment.id}' n'est pas connecté.")
        return errors
    
    #transforme le réseau d'équipement en un réseau hydraulique---------------------------------------------------------------
    def to_hydraulic_network(self) -> HydraulicNetwork:
        hydraulic_network = HydraulicNetwork()
        #ajoute les composants de chaque équipement au réseau hydraulique
        for equipment in self.equipments:
            components = equipment.generate_hydraulic_representation(self.connections)
            for component in components:
                #ajoute le composant au réseau hydraulique
                if isinstance(component, (Junction, Reservoir)): #si c'est un noeud
                    #vérifie que le nœud n'existe pas déjà dans le réseau, si il n'existe pas, l'ajoute
                    if component.id not in hydraulic_network.nodes: 
                        hydraulic_network.add_node(component) 
                else: #si c'est un lien
                    hydraulic_network.add_link(component)
        return hydraulic_network
    
    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_results_from_hydraulic_network(self, network: HydraulicNetwork):
        for equipment in self.equipments:
            equipment.get_simulation_results(network, self.connections)
    
    #Représentation textuelle du réseau d'équipement
    def __str__(self) -> str:
        equipment_str = "\n".join(str(eq) for eq in self.equipments)
        connections_str = "\n".join(f"  Port '{port_id}' connecté via '{conn_name}'" for port_id, conn_name in self.connections.items())
        return (
            f"=========================================================================================\n"
            f"Description du reseau d'équipement hydraulique NetworkEquipment(id='{self.id}'):\n"
            f"=========================================================================================\n"
            
            f"\nEquipments composants le réseau:\n "
            f". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .\n"
            f"{equipment_str}"
            
            f"\nConnexions dans le réseau d'équipement:\n"
            f". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ."
            f"\n{connections_str}\n"
            )


#===================================================================================================================================
#Test simple de la classe NetworkEquipment------------------------------------------------------------------------------------------
#==================================================================================================================================== 

if __name__ == "__main__":  
    # Créer un réseau d'équipement
    network_eq = NetworkEquipment("Network1")
    
    # Créer des équipements
    #pump_eq = PumpEquipment("Pump1", curve_points=[(50, 15), (100, 10)], elevation=5.0)
    pressure_High = PressureBoundaryConditionEquipment("PressureBC1", pressure_bar=3.0, elevation=10.0)
    pressure_Low = PressureBoundaryConditionEquipment("PressureBC2", pressure_bar=1.0, elevation=10.0)
    pipe_1 = PipeConnectionEquipment("Pipe1", length=20.0, diameter=0.15, roughness=110)
    pipe_2 = PipeConnectionEquipment("Pipe2", length=20.0, diameter=0.15, roughness=110)

    # Ajouter les équipements au réseau
    network_eq.add_equipment(pressure_High)
    network_eq.add_equipment(pressure_Low)
    network_eq.add_equipment(pipe_1)
    network_eq.add_equipment(pipe_2)


    # Connecter les équipements via leurs ports
    network_eq.connectEquipments(pressure_High, pressure_High.ports[f"{pressure_High.id}_P1"], pipe_1, pipe_1.ports[f"{pipe_1.id}_P1"])  # Connecter la sortie de la pompe à l'entrée du tuyau
    network_eq.connectEquipments(pipe_1, pipe_1.ports[f"{pipe_1.id}_P2"], pipe_2, pipe_2.ports[f"{pipe_2.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression
    network_eq.connectEquipments(pipe_2, pipe_2.ports[f"{pipe_2.id}_P2"], pressure_Low, pressure_Low.ports[f"{pressure_Low.id}_P1"])  # Connecter la sortie du tuyau à la condition de bord pression

    # Afficher les équipements et leurs connexions
    for eq in network_eq.equipments:
        print(eq)
        for port in eq.ports:
            print(f"  {port}")
    print("Connexions dans le réseau d'équipement:")
    for port_id, conn_name in network_eq.connections.items():
        print(f"  Port '{port_id}' connecté via '{conn_name}'")

    # Valider le réseau d'équipement
    print("Validation réseau d'équipement:", network_eq.validate_flowcad())

    # Convertir en réseau hydraulique
    hydraulic_network = network_eq.to_hydraulic_network()
    print("Réseau hydraulique créé avec succès.")
    print(hydraulic_network)
    print("Validation réseau hydraulique:", hydraulic_network.validate_flowcad())


    #convertir en modèle WNTR
    wn_network = hydraulic_network.to_wntr()
    print("Modèle WNTR créé avec succès.")
    # Afficher les nœuds et liens WNTR
    print("Nœuds WNTR:", wn_network.nodes)    
    print("Liens WNTR:", wn_network.links)
    #Exécuter une simulation simple avec WNTR
    import wntr

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

            # Afficher les résultats
    """
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
        """