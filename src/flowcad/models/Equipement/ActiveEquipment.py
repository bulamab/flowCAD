from .BaseEquipment import BaseEquipment, Port
from typing import List, Dict, Any, Optional
from ..hydraulique.components import HydraulicComponent
from ..hydraulique.links import Pump
from ..hydraulique.nodes import Junction, Reservoir
from ..fluid import Fluid
from ..HydraulicConverter import *  

"""Classe pour les équipements actifs (ex: pompes, vannes)"""

#Classe pour une pompe---------------------------------------------------------------------------------------------
class PumpEquipment(BaseEquipment):
    def __init__(self, id: str, curve_points: List[tuple[float, float]] = None, elevation: float = 0.0):
        super().__init__(id) #initialisation de la classe de base

        #la courbe de la pompe est une liste de tuples (débit, hauteur)
        if curve_points is None:
            #courbe par défaut si non fournie
            self.pump_curve = [(40, 10)]
        else:
            self.pump_curve = curve_points

        #hauteur d'installation de la pompe
        self.elevation = elevation  # élévation en mètres

        #creation de deux ports pour la pompe à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        Port2 = Port(port_id=f"{id}_P2", parent_equipment_id=id)
        #ajout des ports à l'équipement
        self.add_port(Port1)
        self.add_port(Port2)
    
    def generate_hydraulic_representation(self) -> List[HydraulicComponent]:
        
        #créeation des jonctions de la pompe
        J1 = Junction(
            component_id=f"{self.id}_J1",
            elevation=self.elevation,
            demand=0.0
        )
        J2 = Junction(
            component_id=f"{self.id}_J2",
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
    
#classe pour une condition au bord type pression---------------------------------------------------------------------------------------------
class PressureBoundaryConditionEquipment(BaseEquipment):
    def __init__(self, id: str, pressure_bar: float = 0.0, elevation: float = 0.0):
        super().__init__(id) #initialisation de la classe de base

        self.pressure_bar = pressure_bar  # pression en bars
        self.elevation = elevation  # élévation en mètres

        #creation d'un port pour la condition au bord à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        #ajout du port à l'équipement
        self.add_port(Port1)
    
    def generate_hydraulic_representation(self) -> List[HydraulicComponent]:
        
        #créeation de la jonction de la condition au bord
        J1 = Junction(
            component_id=f"{self.id}_J1",
            elevation=self.elevation,
            demand=0.0
        )
        R1 = Reservoir(
            component_id=f"{self.id}_R1",
            head=HydraulicConverter.pressure_to_head(self.pressure_bar, self.elevation),
            elevation=self.elevation    
        )

        return [J1, R1]
    
    #Représentation textuelle de l'équipement
    def __str__(self) -> str:
        return f"PressureBoundaryConditionEquipment(id='{self.id}', pressure_bar={self.pressure_bar}, elevation={self.elevation})"
    

#test simple de la classe PumpEquipment
if __name__ == "__main__":

    #Test de la pompe
    print("Test de la pompe:")
    pump_eq = PumpEquipment(id="Pump1")
    #print(pump_eq)
    print("Représentation hydraulique:")
    for component in pump_eq.generate_hydraulic_representation():
        print(component)
    
    #Test de la condition au bord de pression
    print("\nTest de la condition au bord de pression:")
    pbc_eq = PressureBoundaryConditionEquipment(id="PBC1", pressure_bar=3.0, elevation=10.0)
    print(pbc_eq)  
    print("Représentation hydraulique:")
    for component in pbc_eq.generate_hydraulic_representation():
        print(component)    
