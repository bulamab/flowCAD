try:
    from .components import HydraulicComponent, HydraulicNode, HydraulicLink
except ImportError:
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
    
    def __init__(self, component_id: str, start_node: str, end_node: str, curve_points: List[tuple[float, float]] = None):
        super().__init__(component_id, start_node, end_node)
        
        if curve_points is None: 
            #courbe par défaut si non fournie
            curve_points = [(40, 10)]
        else:
            self.curve_points = curve_points

    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not (
                isinstance(self.curve_points, list) and
                len(self.curve_points) == 1 and
                isinstance(self.curve_points[0], tuple) and 
                len(self.curve_points[0]) == 2 and
                all(isinstance(pt, (int, float)) for pt in self.curve_points[0])
        ):
            errors.append("La courbe doit être une liste de un seul tuple (débit, hauteur)")
        
        return errors
    
    def to_wntr(self, wn_network):

        #Courbe de pompe avec un seul point (Q, H)
        curve_name = f"{self.id}_curve"
        wn_network.add_curve(
            name=curve_name,
            curve_type='HEAD',
            xy_tuples_list=self.curve_points
        )
        wn_network.add_pump(
            name=self.id,
            start_node_name=self.start_node,
            end_node_name=self.end_node,
            pump_type='HEAD',
            pump_parameter=curve_name
        )
        return wn_network.get_link(self.id)    
    
#Test simple de la classe Pipe
if __name__ == "__main__":  
    # Créer un tuyau
    p1 = Pipe("P1", start_node="J1", end_node="J2", length=100.0, diameter=0.3, roughness=100)
    print(p1)
    print("Validation tuyau:", p1.validate_flowcad())  
    # Créer une pompe
    pu1 = Pump("PU1", start_node="J2", end_node="J3", curve_points=[(10, 40)])
    print(pu1)
    print("Validation pompe:", pu1.validate_flowcad())