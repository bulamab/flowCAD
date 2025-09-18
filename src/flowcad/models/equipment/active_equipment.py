from typing import List, Dict, Any, Optional

from .base_equipment import BaseEquipment, Port
from ..hydraulique.components import HydraulicComponent
from ..hydraulique.links import Pump, Pipe
from ..hydraulique.nodes import Junction, Reservoir
from ..hydraulique.network import HydraulicNetwork
from ..fluid import Fluid
from ..hydraulic_converter import *  


"""Classe pour les équipements actifs (ex: pompes, vannes)"""

#----------------------------------------------------------------#
#equipements actifs:
#- PupmpEquipment: une pompe avec une courbe caractéristique
#- PressureBoundaryConditionEquipment: une condition aux limites de type pression (réservoir)
#- FlowRateBoundaryConditionEquipment: une condition aux limites de type débit volumique (entrée/sortie de fluide)
#- HydraulicResistanceEquipment: une résistance hydraulique singulière (consommateur de chaleur, producteur de chaleur, etc. )

#===============================================================================================================================================
#Classe pour une pompe---------------------------------------------------------------------------------------------
#===============================================================================================================================================

class PumpEquipment(BaseEquipment):
    def __init__(self, id: str, curve_points: List[tuple[float, float]] = None, elevation: float = 0.0):
        super().__init__(id) #initialisation de la classe de base

        #la courbe de la pompe est une liste de tuples (débit, hauteur)
        if curve_points is None:
            #courbe par défaut si non fournie
            self.pump_curve = [(40, 20)]
        else:
            self.pump_curve = curve_points

        #hauteur d'installation de la pompe
        self.elevation = elevation  # élévation en mètres

        #creation de deux ports pour la pompe à partir de l'id de l'équipement
        #Convetion de nommage des ports: <id_equipement>_P1 pour l'entrée, <id_equipement>_P2 pour la sortie
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        Port2 = Port(port_id=f"{id}_P2", parent_equipment_id=id)
        #ajout des ports à l'équipement
        self.add_port(Port1)
        self.add_port(Port2)

        #variables pour stocker les résultats de la simulation
        self.flowrate: Optional[float] = None  # le débit fourni par la pompe en m³/s
        self.head_gain: Optional[float] = None  # la hauteur manoméctrique fournie par la pompe en mètres
        #pressions et charge aux noeuds d'entrée et de sortie
        self.head_1: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_1: Optional[float] = None # la pression au noeud en kPa
        self.head_2: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_2: Optional[float] = None # la pression au noeud en kPa
    
    def generate_hydraulic_representation(self, connections: Dict[str, str]) -> List[HydraulicComponent]:
        
        #créeation des jonctions de la pompe
        #noeud pour l'entrée de la pompe
        J1 = Junction(
            component_id=connections[f"{self.id}_P1"],
            elevation=self.elevation,
            demand=0.0
        )
        #noeud pour la sortie de la pompe
        J2 = Junction(
            component_id=connections[f"{self.id}_P2"],
            elevation=self.elevation,
            demand=0.0
        )

        pump = Pump(
            component_id=self.id,
            start_node=J1.id,
            end_node=J2.id,
            curve_points=self.pump_curve
        )
        return [J1, J2, pump]
    
    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_simulation_results(self, network: HydraulicNetwork, connections: Dict[str, str]):

        #Resultats de débit et gain de hauteur de la pompe
        if self.id in network.links:
            link = network.links[self.id]
            self.flowrate = link.flowrate
            #self.head_gain = link.headloss
        else:  #si le lien n'est pas trouvé, réinitialiser les résultats
            self.flowrate = None    
            #self.head_gain = None
        #resultats de pression et hauteur au noeud d'entrée
        IdEquiv_P1 = connections[f"{self.id}_P1"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        IdEquiv_P2 = connections[f"{self.id}_P2"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        if IdEquiv_P1 in network.nodes: 
            node1 = network.nodes[IdEquiv_P1]
            node2 = network.nodes[IdEquiv_P2]
            self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_kPa(node1.pressure)
            self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_kPa(node2.pressure)
            self.ports[f"{self.id}_P1"].head = HydraulicConverter.P_mCE_to_kPa(node1.head)
            self.ports[f"{self.id}_P2"].head = HydraulicConverter.P_mCE_to_kPa(node2.head)
            self.pressure_1 = HydraulicConverter.P_mCE_to_kPa(node1.pressure)
            self.head_1 = HydraulicConverter.P_mCE_to_kPa(node1.head)
            self.pressure_2 = HydraulicConverter.P_mCE_to_kPa(node2.pressure)
            self.head_2 = HydraulicConverter.P_mCE_to_kPa(node2.head)
            self.head_gain = self.head_2 - self.head_1 #en kPa
        else:
            self.ports[f"{self.id}_P1"].pressure = None
            self.ports[f"{self.id}_P2"].pressure = None
            self.ports[f"{self.id}_P1"].head = None
            self.ports[f"{self.id}_P2"].head = None  
            self.head_1 = None
            self.pressure_1 = None
            self.head_2 = None
            self.pressure_2 = None
            self.head_gain

    #Représentation textuelle de l'équipement
    def __str__(self) -> str:

        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type Pompe PumpEquipment(BaseEquipment):\n"
            f"Propriétés:\n"
            f"-> id='{self.id}'," 

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}, "
            f"Port2: {self.ports[f'{self.id}_P2']})\n"
            f"Résultats de la simulation:\n"
            f"-> flowrate={self.flowrate} (m3/s), headGain={self.head_gain} (m)\n"
            f"-------------------------------------------------------------"
        )
#===============================================================================================================================================
#classe pour une condition au bord type pression---------------------------------------------------------------------------------------------
#===============================================================================================================================================

class PressureBoundaryConditionEquipment(BaseEquipment):
    def __init__(self, id: str, pressure_bar: float = 0.0, elevation: float = 0.0):
        super().__init__(id) #initialisation de la classe de base

        self.pressure_bar = pressure_bar  # pression en bars
        self.elevation = elevation  # élévation en mètres

        #creation d'un port pour la condition au bord à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        #ajout du port à l'équipement
        self.add_port(Port1)

        #variables pour stocker les résultats de la simulation
        self.head_1: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure_1: Optional[float] = None # la pression au noeud en kPa

    
    def generate_hydraulic_representation(self,  connections: Dict[str, str]) -> List[HydraulicComponent]:
        

        R1 = Reservoir(
            component_id=connections[f"{self.id}_P1"],
            head=HydraulicConverter.pressure_to_head(self.pressure_bar, self.elevation),
            elevation=self.elevation    
        )

        return [R1]
    
    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_simulation_results(self, network: HydraulicNetwork, connections: Dict[str, str]):

        IdEquiv = connections[f"{self.id}_P1"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        if IdEquiv in network.nodes:
            node = network.nodes[IdEquiv]
            self.head_1 = HydraulicConverter.P_mCE_to_kPa(node.head) #la pression est convertie avant d'être affichée!
            #par défaut, basé sur un élément WNTR du type réservoir, qui ne spécifie que la charge totale
            #la pression et l'élévation ne sont pas spécifiées. Il semblerait que WNTR considère la charge comme 100% due à la hauteur
            #dans notre cas, on considère une élévation de base, et donc  on en déduit la pression
            self.pressure_1 = HydraulicConverter.P_mCE_to_kPa(node.head-self.elevation) #la pression est convertie avant d'être affichée!

    #Représentation textuelle de l'équipement
    def __str__(self) -> str:
        
        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type Cond. lim. pression: PressureBoundaryConditionEquipment(BaseEquipment):\n"
            f"Propriétés:\n"
            f"-> id='{self.id}',"
            f"pressure_bar={self.pressure_bar},"
            f"elevation={self.elevation}\n" 

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}\n "
            f"Résultats de la simulation:\n"
            f"-> head_1={self.head_1} (kPa), pressure_1={self.pressure_1} (kPa)\n"
            f"-------------------------------------------------------------"
        )

#===============================================================================================================================================
#Classe pour une condition  aux limites de type débit volumique
#===============================================================================================================================================

class FlowRateBoundaryConditionEquipment(BaseEquipment):

    """Classe pour une condition aux limites de type débit volumique
    Un débit volumique positif signifie que le fluide entre dans le réseau, tandis qu'un débit négatif signifie qu'il en sort."""

    def __init__(self, id: str, flowrate_m3s: float = 0.0, elevation: float = 0.0):
        super().__init__(id) #initialisation de la classe de base

        self.flowrate_m3s = flowrate_m3s  # débit en m³/s
        self.elevation = elevation  # élévation en mètres

        #creation d'un port pour la condition au bord à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        #ajout du port à l'équipement
        self.add_port(Port1)

        #variables pour stocker les résultats de la simulation
        self.head: Optional[float] = None  # la charge totale du fluide, en kPa
        self.pressure: Optional[float] = None # la pression au noeud en kPa

    
    def generate_hydraulic_representation(self,  connections: Dict[str, str]) -> List[HydraulicComponent]:
        

        J1 = Junction(
            component_id=connections[f"{self.id}_P1"],
            elevation=self.elevation,
            demand=-self.flowrate_m3s  # le débit est négatif car c'est une entrée dans le réseau
        )

        return [J1]
    
    #methode pour obtenirs les résutlats de la simulation depuis le réseau hydraulique
    def get_simulation_results(self, network: HydraulicNetwork, connections: Dict[str, str]):

        IdEquiv = connections[f"{self.id}_P1"] #va chercher l'id du noeud équivalent dans le réseau hydraulique
        if IdEquiv in network.nodes:
            node = network.nodes[IdEquiv]
            self.head = HydraulicConverter.P_mCE_to_kPa(node.head) #la pression est convertie avant d'être affichée!
            #par défaut, basé sur un élément WNTR du type jonction, qui ne spécifie que la charge totale
            #la pression et l'élévation ne sont pas spécifiées. Il semblerait que WNTR considère la charge comme 100% due à la hauteur
            #dans notre cas, on considère une élévation de base, et donc  on en déduit la pression
            self.pressure = HydraulicConverter.P_mCE_to_kPa(node.head-self.elevation)

    #représentation textuelle
    def __str__(self) -> str:
        
        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type Cond. lim. débit: FlowRateBoundaryConditionEquipment(BaseEquipment):\n"
            f"Propriétés:\n"
            f"-> id='{self.id}',"
            f"flowrate_m3s={self.flowrate_m3s},"
            f"elevation={self.elevation}\n" 

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}\n "
            f"Résultats de la simulation:\n"
            f"-> head={self.head} (kPa), pressure={self.pressure} (kPa)\n"
            f"-------------------------------------------------------------"
        )
    
#===============================================================================================================================================
#classe pour une résistance hydraulique singulière (consommateur de chaleur, producteur de chaleur, etc. )
#===============================================================================================================================================
class HydraulicResistanceEquipment(BaseEquipment):

    """Classe représentant un équipement de résistance hydraulique.
    Une résistance hydraulique est représentée comme un tuyau de longeur nulle, avec un coefficient de pertes de charges singulières
    Le coefficient de perte de charge singulière peut être donné de différentes manières via la classe hydraulic_converter"""

    def __init__(self, id: str, diameter: float, zeta: float = 0.0, elevation: float = 0.0):
        super().__init__(id)

        self.length = 0.01  # une petite longueur en mètres
        self.diameter = diameter  # diamètre en mètres 
        self.roughness = 0.000001  # rugosité en mm faibles, là aussi pour éviter l'effet des pertes de charges linéaires
        self.elevation = elevation #l'élévation du tuyau (par défaut, on considère qu'il est horizontal l'élvation est adaptés lors des connections aux équipements)
        self.zeta = zeta #le coefficient zeta, qui permet d'obtenir les pertes de charges en Pa

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
        """ Du point de vue hydraulique, représenté comme un tuyau, avec juste des pertes singulières"""
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

        pipe = Pipe(
            component_id=self.id,
            start_node=J1.id,
            end_node=J2.id,
            length=self.length,
            diameter=self.diameter,
            minor_loss=self.zeta,
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
        if IdEquiv_P1 in network.nodes:
            node1 = network.nodes[IdEquiv_P1]
            node2 = network.nodes[IdEquiv_P2]
            
            self.ports[f"{self.id}_P1"].head = HydraulicConverter.P_mCE_to_kPa(node1.head)
            self.ports[f"{self.id}_P2"].head = HydraulicConverter.P_mCE_to_kPa(node2.head)
            #self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_kPa(node1.pressure)
            #self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_kPa(node2.pressure)
            self.ports[f"{self.id}_P1"].pressure = HydraulicConverter.P_mCE_to_kPa(node1.head-node1.elevation)
            self.ports[f"{self.id}_P2"].pressure = HydraulicConverter.P_mCE_to_kPa(node2.head-node2.elevation)
            self.pressure_1 = HydraulicConverter.P_mCE_to_kPa(node1.head-node1.elevation) #la pression est convertie avant d'être affichée!
            self.head_1 = HydraulicConverter.P_mCE_to_kPa(node1.head) #la pression est convertie avant d'être affichée!
            self.pressure_2 = HydraulicConverter.P_mCE_to_kPa(node2.head-node2.elevation) #la pression est convertie avant d'être affichée!
            self.head_2 = HydraulicConverter.P_mCE_to_kPa(node2.head) # la pression est convertie avant d'être affichée!
            self.total_headloss = self.head_1 - self.head_2 #en kPa
        else:  #si le noeud n'est pas trouvé, réinitialiser les résultats
            self.ports[f"{self.id}_P1"].pressure = None
            self.ports[f"{self.id}_P2"].pressure = None
            self.ports[f"{self.id}_P1"].head = None
            self.ports[f"{self.id}_P2"].head = None
            self.head_1 = None
            self.pressure_1 = None
            self.head_2 = None  
            self.pressure_2 = None
            self.total_headloss = None
        
    
    #Représentation textuelle de l'équipement
    def __str__(self) -> str:   
        return (
            f"-------------------------------------------------------------\n"
            f"Equipement du type résistance singulière HydraulicResistanceEquipment(BaseEquipment):\n"
            f"Propriétés:\n"
            f"-> id='{self.id}'," 
            f"diameter={self.diameter},"

            f"Ports de {self.id} :\n"
            f"-> Port1: {self.ports[f'{self.id}_P1']}, "
            f"Port2: {self.ports[f'{self.id}_P2']})\n"

            f"Résultats de la simulation:\n"
            f"-> flowrate={self.flowrate} (m3/s), velocity={self.velocity} (m/s)\n"
            f"-------------------------------------------------------------"
        )