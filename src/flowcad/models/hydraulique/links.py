from components import HydraulicComponent, HydraulicNode, HydraulicLink
from typing import List 

class Pipe(HydraulicLink):
    """
    Classe représentant un tuyau hydraulique.
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str, length: float, diameter: float, roughness: float):
        super().__init__(component_id, start_node, end_node)
        self.length = length  # en mètres
        self.diameter = diameter  # en mètres
        self.roughness = roughness  # en mm
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.length, (int, float)) or self.length <= 0:
            errors.append("La longueur doit être un nombre positif")
        
        if not isinstance(self.diameter, (int, float)) or self.diameter <= 0:
            errors.append("Le diamètre doit être un nombre positif")
        
        if not isinstance(self.roughness, (int, float)) or self.roughness < 0:
            errors.append("La rugosité doit être un nombre non négatif")
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_pipe(
            name=self.id,
            start_node_name=self.start_node,
            end_node_name=self.end_node,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness
        )
        return wn_network.get_link(self.id)

class Pump(HydraulicLink):
    """
    Classe représentant une pompe hydraulique.
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str, power: float):
        super().__init__(component_id, start_node, end_node)
        self.power = power  # en kW
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.power, (int, float)) or self.power <= 0:
            errors.append("La puissance doit être un nombre positif")
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_pump(
            name=self.id,
            start_node=self.start_node,
            end_node=self.end_node,
            pump_type='POWER',
            power=self.power
        )
        return wn_network.get_link(self.id)    
    
#Test simple de la classe Pipe
if __name__ == "__main__":  
    # Créer un tuyau
    p1 = Pipe("P1", start_node="J1", end_node="J2", length=100.0, diameter=0.3, roughness=100)
    print(p1)
    print("Validation tuyau:", p1.validate_flowcad())  