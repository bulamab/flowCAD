from platform import node
from typing import List, Dict, Any, Optional

from .base_equipment import BaseEquipment, Port
from ..hydraulique.components import HydraulicComponent
from ..hydraulique.links import Pump, Pipe
from ..hydraulique.nodes import Junction, Reservoir
from ..hydraulique.network import HydraulicNetwork
from ..fluid import Fluid
from ..hydraulic_converter import *  

"""Classe pour les connections entre équipements"""

#défintion des équipements de connection (tuyaux, Té, coudes, etc.)
#- PipeConnectionEquipment: un tuyau de connection entre deux équipements
#- TeeConnectionEquipment: un Té de connection entre trois équipements


#===============================================================================================================================================
#tuyau de connection entre deux équipements---------------------------------------------------------------------------------------------
#===============================================================================================================================================

class PipeConnectionEquipment(BaseEquipment):
    def __init__(self, id: str, length: float = 1.0, diameter: float = 0.1, roughness: float = 100, elevation: float = 0):
        super().__init__(id) #initialisation de la classe de base

        self.length = length  # longueur en mètres
        self.diameter = diameter  # diamètre en mètres
        self.roughness = roughness  # rugosité en mm
        self.elevation = elevation #l'élévation du tuyau (par défaut, on considère qu'il est horizontal l'élvation est adaptés lors des connections aux équipements)

        #creation de deux ports pour le tuyau de connection à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        Port2 = Port(port_id=f"{id}_P2", parent_equipment_id=id)
        #ajout des ports à l'équipement
        self.add_port(Port1)
        self.add_port(Port2)
        #variables pour stocker les résultats de la simulation
        self.flowrate: Optional[float] = None  # le débit dans le tuyau en m³/s
        self.velocity: Optional[float] = None  # la vitesse dans le tuyau en m/s
        self.headloss: Optional[float] = None  # la perte de charge dans le tuyau Pa/m
        self.frictionfactor: Optional[float] = None  # le facteur de friction de Darcy-Weisbach
        #pressions et charge aux noeuds d'entrée et de sortie
        self.head_1: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_1: Optional[float] = None # la pression au noeud en kPa
        self.head_2: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_2: Optional[float] = None # la pression au noeud en kPa
        self.total_headloss: Optional[float] = None #la perte de charge totale en kPa (headloss * longueur)

    def generate_hydraulic_representation(self, connections: Dict[str, str]) -> List[HydraulicComponent]:
        
        #créeation des jonctions
        J1 = Junction(
            component_id=connections[f"{self.id}_P1"],
            elevation=self.elevation,
            demand=0.0
        )
        J2 = Junction(
            component_id=connections[f"{self.id}_P2"],
            elevation=self.elevation,
            demand=0.0
        )

        pipe = Pipe(
            component_id=self.id,
            start_node=J1.id,
            end_node=J2.id,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness/1000 #passage de mm en m, pour calculs selon WNTR
        )
        return [J1, J2, pipe]
    
    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_simulation_results(self, network: HydraulicNetwork, connections: Dict[str, str]):

        #Resultats de débit et perte de charge du tuyau
        if self.id in network.links:
            link = network.links[self.id]
            self.flowrate = link.flowrate
            self.headloss = HydraulicConverter.P_mCE_to_Pa(link.headloss)
            self.velocity = link.velocity
            self.frictionfactor = link.frictionfactor
        else:  #si le lien n'est pas trouvé, réinitialiser les résultats
            self.flowrate = None
            self.headloss = None
            self.velocity = None
            self.frictionfactor = None

        #resultats de pression aux noeuds de connexion
        IdEquiv_P1 = connections[f"{self.id}_P1"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        IdEquiv_P2 = connections[f"{self.id}_P2"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        if IdEquiv_P1 and IdEquiv_P2 in network.nodes:
            node1 = network.nodes[IdEquiv_P1]
            node2 = network.nodes[IdEquiv_P2]
            
            self.ports[f"{self.id}_P1"].head = HydraulicConverter.P_mCE_to_Pa(node1.head)
            self.ports[f"{self.id}_P2"].head = HydraulicConverter.P_mCE_to_Pa(node2.head)
            #self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_Pa(node1.pressure)
            #self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_Pa(node2.pressure)
            self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_Pa(node1.head-node1.elevation)
            self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_Pa(node2.head-node2.elevation)
            self.head_1 = HydraulicConverter.P_mCE_to_Pa(node1.head) #la pression est convertie avant d'être affichée!
            self.pressure_1 = HydraulicConverter.P_mCE_to_Pa(node1.head-node1.elevation) #la pression est convertie avant d'être affichée!
            self.head_2 = HydraulicConverter.P_mCE_to_Pa(node2.head) #la pression est convertie avant d'être affichée!
            self.pressure_2 = HydraulicConverter.P_mCE_to_Pa(node2.head-node2.elevation) #la pression est convertie avant d'être affichée!
            self.total_headloss = self.head_1 - self.head_2 #en Pa
        else:  #si le noeud n'est pas trouvé, réinitialiser les résultats
            self.ports[f"{self.id}_P1"].pressure = None
            self.ports[f"{self.id}_P2"].pressure = None
            self.ports[f"{self.id}_P1"].head = None
            self.ports[f"{self.id}_P2"].head = None
            self.total_headloss = None
            self.head_1 = None
            self.pressure_1 = None
            self.head_2 = None
            self.pressure_2 = None
    #Représentation textuelle de l'équipement
    def __str__(self) -> str:   
        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type tuyau PipeConnectionEquipment():\n"
            f"Propriétés:\n"
            f"-> id='{self.id}'," 
            f"length={self.length},"
            f"diameter={self.diameter},"
            f"roughness={self.roughness}\n"

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}, "
            f"Port2: {self.ports[f'{self.id}_P2']})\n"

            f"Résultats de la simulation:\n"
            f"-> flowrate={self.flowrate} (m3/s), headloss={self.headloss} (Pa/m), velocity={self.velocity} (m/s), frictionfactor={self.frictionfactor} ()\n"
            f"-------------------------------------------------------------"
        )
    
#===============================================================================================================================================
#classe qui définit un T (qui permet de connecter 3 appareils/tuyaux au même endroit)
#===============================================================================================================================================
class TeeConnectionEquipment(BaseEquipment):

    def __init__(self, id: str, diameter: float, elevation: float = 0):
        super().__init__(id)
        self.diameter = diameter
        self.elevation = elevation #l'élévation du Té (milieu)
        self.length = 0.01  # longueur fictive pour le calcul des pertes de charge, en mètres
        self.roughness = 0.0000001 #fictif pour limiter les pertes de charges

        #creation de deux ports pour le tuyau de connection à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        Port2 = Port(port_id=f"{id}_P2", parent_equipment_id=id)
        Port3 = Port(port_id=f"{id}_P3", parent_equipment_id=id) #le port du "milieu"
        #ajout des ports à l'équipement
        self.add_port(Port1)
        self.add_port(Port2)
        self.add_port(Port3)
        #variables pour stocker les résultats de la simulation
        self.flowrate_1: Optional[float] = None  # le débit dans le tuyau P1 en m³/s
        self.flowrate_2: Optional[float] = None  # le débit dans le tuyau P2 en m³/s
        self.flowrate_3: Optional[float] = None  # le débit dans le tuyau P3 en m³/s
        #variables pour stocker les résultats de la simulation
        self.head_1: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_1: Optional[float] = None # la pression au noeud en kPa
        self.head_2: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_2: Optional[float] = None # la pression au noeud
        self.head_3: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_3: Optional[float] = None # la pression au noeud en kPa

    def generate_hydraulic_representation(self, connections: Dict[str, str]) -> List[HydraulicComponent]:
        
        #créeation des jonctions de la pompe
        J1 = Junction(
            component_id=connections[f"{self.id}_P1"],
            elevation=self.elevation,
            demand=0.0
        )
        J2 = Junction(
            component_id=connections[f"{self.id}_P2"],
            elevation=self.elevation,
            demand=0.0
        )
        J3 = Junction(  
            component_id=connections[f"{self.id}_P3"],
            elevation=self.elevation,
            demand=0.0
        )
        #le noeud du milieu
        J4 = Junction(
            component_id=f"{self.id}_Mid",
            elevation=self.elevation,
            demand=0.0
        )

        pipe1 = Pipe(
            component_id=f"{self.id}_Pipe1",
            start_node=J1.id,
            end_node=J4.id,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness/1000 #passage de mm en m, pour calculs selon WNTR
        )
        pipe2 = Pipe(
            component_id=f"{self.id}_Pipe2",
            start_node=J2.id,
            end_node=J4.id,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness/1000 #passage de mm en m, pour calculs selon WNTR
        )
        pipe3 = Pipe(
            component_id=f"{self.id}_Pipe3",
            start_node=J3.id,
            end_node=J4.id,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness/1000 #passage de mm en m, pour calculs selon WNTR
        )
        return [J1, J2, J3, J4, pipe1, pipe2, pipe3]

    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_simulation_results(self, network: HydraulicNetwork, connections: Dict[str, str]):

        #Resultats de débit et perte de charge du tuyau
        if f"{self.id}_Pipe1" in network.links:
            link = network.links[f"{self.id}_Pipe1"]
            self.flowrate_1 = link.flowrate
        else:  #si le lien n'est pas trouvé, réinitialiser les résultats
            self.flowrate_1 = None
        if f"{self.id}_Pipe2" in network.links:
            link = network.links[f"{self.id}_Pipe2"]
            self.flowrate_2 = link.flowrate
        else:  #si le lien n'est pas trouvé, réinitialiser les résultats
            self.flowrate_2 = None
        if f"{self.id}_Pipe3" in network.links:
            link = network.links[f"{self.id}_Pipe3"]
            self.flowrate_3 = link.flowrate
        else:  #si le lien n'est pas trouvé, réinitialiser les résultats
            self.flowrate_3 = None

        #resultats de pression aux noeuds de connexion
        IdEquiv_P1 = connections[f"{self.id}_P1"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        IdEquiv_P2 = connections[f"{self.id}_P2"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        IdEquiv_P3 = connections[f"{self.id}_P3"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        Id4 = f"{self.id}_Mid"
        if IdEquiv_P1 and IdEquiv_P2 and IdEquiv_P3 in network.nodes:
            node1 = network.nodes[IdEquiv_P1]
            node2 = network.nodes[IdEquiv_P2]
            node3 = network.nodes[IdEquiv_P3]
            node4 = network.nodes[Id4]
            self.ports[f"{self.id}_P1"].head = HydraulicConverter.P_mCE_to_Pa(node1.head)
            self.ports[f"{self.id}_P2"].head = HydraulicConverter.P_mCE_to_Pa(node2.head)
            self.ports[f"{self.id}_P3"].head = HydraulicConverter.P_mCE_to_Pa(node3.head)
            #self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_Pa(node1.pressure)
            #self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_Pa(node2.pressure)
            self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_Pa(node1.head-node1.elevation)
            self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_Pa(node2.head-node2.elevation)
            self.ports[f"{self.id}_P3"].pressure = HydraulicConverter.P_mCE_to_Pa(node3.head-node3.elevation)
            self.head_1 = HydraulicConverter.P_mCE_to_Pa(node1.head) #la pression est convertie avant d'être affichée!
            self.pressure_1 = HydraulicConverter.P_mCE_to_Pa(node1.head-node1.elevation) #la pression est convertie avant d'être affichée!
            self.head_2 = HydraulicConverter.P_mCE_to_Pa(node2.head) #la pression est convertie avant d'être affichée!
            self.pressure_2 = HydraulicConverter.P_mCE_to_Pa(node2.head-node2.elevation) #la pression est convertie avant d'être affichée!
            self.head_3 = HydraulicConverter.P_mCE_to_Pa(node3.head) #la pression est convertie avant d'être affichée!
            self.pressure_3 = HydraulicConverter.P_mCE_to_Pa(node3.head-node3.elevation) #la pression est convertie avant d'être affichée!
        else:  #si le noeud n'est pas trouvé, réinitialiser les résultats
            self.ports[f"{self.id}_P1"].pressure = None
            self.ports[f"{self.id}_P2"].pressure = None
            self.ports[f"{self.id}_P3"].pressure = None
            self.ports[f"{self.id}_P1"].head = None
            self.ports[f"{self.id}_P2"].head = None
            self.ports[f"{self.id}_P3"].head = None
            self.head_1 = None
            self.pressure_1 = None
            self.head_2 = None
            self.pressure_2 = None
            self.head_3 = None
            self.pressure_3 = None

    #Représentation textuelle de l'équipement
    def __str__(self) -> str:   
        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type Te TeeConnectionEquipment(BaseEquipment):\n"
            f"Propriétés:\n"
            f"-> id='{self.id}'," 

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}, "
            f"-> Port2: {self.ports[f'{self.id}_P2']}), "
            f"-> Port3: {self.ports[f'{self.id}_P3']})\n"

            f"Résultats de la simulation:\n"
            f"-> flowratePipe1={self.flowrate_1} (m3/s)\n"
            f"-> flowratePipe2={self.flowrate_2} (m3/s)\n"
            f"-> flowratePipe3={self.flowrate_3} (m3/s)\n"
            f"-------------------------------------------------------------"
        )

#Test simple de la classe PipeConnectionEquipment---------------------------------------------------------------------------------------------
if __name__ == "__main__":  
    # Créer un tuyau de connection
    pipe_conn = PipeConnectionEquipment("PipeConn1", length=10.0, diameter=0.2, roughness=120)
    print(pipe_conn)
    # Générer la représentation hydraulique
    """components = pipe_conn.generate_hydraulic_representation()
    for comp in components:
        print(comp)"""