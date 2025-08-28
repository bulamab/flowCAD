from .BaseEquipment import BaseEquipment, Port
from typing import List, Dict, Any, Optional
from ..hydraulique.components import HydraulicComponent
from ..hydraulique.links import Pump, Pipe
from ..hydraulique.nodes import Junction, Reservoir
from ..fluid import Fluid
from ..HydraulicConverter import *  

"""Classe pour les connections entre équipements"""

#tuyau de connection entre deux équipements---------------------------------------------------------------------------------------------
class PipeConnectionEquipment(BaseEquipment):
    def __init__(self, id: str, length: float = 1.0, diameter: float = 0.1, roughness: float = 100):
        super().__init__(id) #initialisation de la classe de base

        self.length = length  # longueur en mètres
        self.diameter = diameter  # diamètre en mètres
        self.roughness = roughness  # rugosité en mm

        #creation de deux ports pour le tuyau de connection à partir de l'id de l'équipement
        Port1 = Port(port_id=f"{id}_P1", parent_equipment_id=id)
        Port2 = Port(port_id=f"{id}_P2", parent_equipment_id=id)
        #ajout des ports à l'équipement
        self.add_port(Port1)
        self.add_port(Port2)
    
    def generate_hydraulic_representation(self) -> List[HydraulicComponent]:
        
        #créeation des jonctions de la pompe
        J1 = Junction(
            component_id=f"{self.id}_J1",
            elevation=0.0,
            demand=0.0
        )
        J2 = Junction(
            component_id=f"{self.id}_J2",
            elevation=0.0,
            demand=0.0
        )

        pipe = Pipe(
            component_id=self.id,
            start_node=J1.id,
            end_node=J2.id,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness
        )
        return [J1, J2, pipe]
    

#Test simple de la classe PipeConnectionEquipment---------------------------------------------------------------------------------------------
if __name__ == "__main__":  
    # Créer un tuyau de connection
    pipe_conn = PipeConnectionEquipment("PipeConn1", length=10.0, diameter=0.2, roughness=120)
    print(pipe_conn)
    # Générer la représentation hydraulique
    components = pipe_conn.generate_hydraulic_representation()
    for comp in components:
        print(comp)