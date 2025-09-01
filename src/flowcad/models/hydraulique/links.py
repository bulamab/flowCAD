try:
    from .components import HydraulicComponent, HydraulicNode, HydraulicLink
except ImportError:
    from components import HydraulicComponent, HydraulicNode, HydraulicLink

from typing import List 

#===============================================================================================================================================
#Definit un tuyau, basé sur HydraulicLink---------------------------------------------------------------------------------
#===============================================================================================================================================

class Pipe(HydraulicLink):
    """
    Classe représentant un tuyau hydraulique.
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str, length: float, diameter: float, roughness: float, minor_loss: float = 0.0, status: str = 'OPEN', check_valve: bool = False):
        super().__init__(component_id, start_node, end_node)
        self.length = length  # en mètres
        self.diameter = diameter  # en mètres
        self.roughness = roughness  # en mètres
        self.minor_loss = minor_loss  # coefficient de perte mineure (idem zeta, mais pour donner au final des pertes de charges en mètres)
        self.status = status  # 'OPEN' ou 'CLOSED'  
        self.check_valve = check_valve  # True ou False

    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.length, (int, float)) or self.length <= 0:
            errors.append("La longueur doit être un nombre positif")
        
        if not isinstance(self.diameter, (int, float)) or self.diameter <= 0:
            errors.append("Le diamètre doit être un nombre positif")
        
        if not isinstance(self.roughness, (int, float)) or self.roughness < 0:
            errors.append("La rugosité doit être un nombre non négatif")

        if not isinstance(self.minor_loss, (int, float)) or self.minor_loss < 0:
            errors.append("La perte mineure doit être un nombre non négatif")
        
        if self.status not in ['OPEN', 'CLOSED']:   
            errors.append("Le statut doit être 'OPEN' ou 'CLOSED'")
        
        if not isinstance(self.check_valve, bool):
            errors.append("La vanne de retenue doit être un booléen (True ou False)")
        
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_pipe(
            name=self.id,
            start_node_name=self.start_node,
            end_node_name=self.end_node,
            length=self.length,
            diameter=self.diameter,
            roughness=self.roughness,
            minor_loss=self.minor_loss,
            initial_status=self.status, 
            check_valve=self.check_valve    
        )
        return wn_network.get_link(self.id)

#===============================================================================================================================================
#définit une pompe, basé sur HydraulicLink---------------------------------------------------------------------------------
#===============================================================================================================================================

class Pump(HydraulicLink):
    """
    Classe représentant une pompe hydraulique.
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str, curve_points: List[tuple[float, float]] = None, Speed: float = 1.0):
        super().__init__(component_id, start_node, end_node)
        
        self.Speed = Speed  # Vitesse de la pompe (facteur multiplicatif)
        if curve_points is None: 
            #courbe par défaut si non fournie
            self.curve_points = [(40, 10)]
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
    
    #représentation textuelle de la pompe
    def __str__(self) -> str:
        return f"Pump(id='{self.id}', start_node='{self.start_node}', end_node='{self.end_node}', curve_points={self.curve_points}, Speed={self.Speed})"
    
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
            pump_parameter=curve_name,
            speed=self.Speed
        )
        return wn_network.get_link(self.id)    

#===============================================================================================================================================
#définit une valve, basé sur HydraulicLink---------------------------------------------------------------------------------
#===============================================================================================================================================

class Valve(HydraulicLink):
    """
    Classe représentant une valve hydraulique.
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str, diameter: float, valve_type: str = 'PRV', setting: float = 0.0, minor_loss: float = 0.0, status: str = 'OPEN'):
        super().__init__(component_id, start_node, end_node)
        self.diameter = diameter  # en mètres
        self.valve_type = valve_type  # 'PRV', 'PSV', 'FCV', 'TCV', 'GPV'
        self.setting = setting  # réglage spécifique au type de valve
        self.minor_loss = minor_loss  # coefficient de perte mineure
        self.status = status  # 'OPEN', 'CLOSED' or 'ACTIVE' (pour les vannes de pression)  

    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.diameter, (int, float)) or self.diameter <= 0:
            errors.append("Le diamètre doit être un nombre positif")
        
        if self.valve_type not in ['PRV', 'PSV', 'FCV', 'TCV', 'GPV']:
            errors.append("Le type de valve doit être l'un des suivants: 'PRV', 'PSV', 'FCV', 'TCV', 'GPV'")
        
        if not isinstance(self.setting, (int, float)):
            errors.append("Le réglage doit être un nombre")
        
        if not isinstance(self.minor_loss, (int, float)) or self.minor_loss < 0:
            errors.append("La perte mineure doit être un nombre non négatif")
        
        if self.status not in ['OPEN', 'CLOSED', 'ACTIVE']:   
            errors.append("Le statut doit être 'OPEN','CLOSED' ou 'ACTIVE'")
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_valve(
            name=self.id,
            start_node_name=self.start_node,
            end_node_name=self.end_node,
            diameter=self.diameter,
            valve_type=self.valve_type,
            initial_setting=self.setting,
            minor_loss=self.minor_loss,
            initial_status=self.status  
        )
        return wn_network.get_link(self.id)

#Test simple de la classe Pipe  and Pump---------------------------------------------------------------------------------
if __name__ == "__main__":  
    # Créer un tuyau
    p1 = Pipe("P1", start_node="J1", end_node="J2", length=100.0, diameter=0.3, roughness=100)
    print(p1)
    print("Validation tuyau:", p1.validate_flowcad())  
    # Créer une pompe
    pu1 = Pump("PU1", start_node="J2", end_node="J3", curve_points=[(10, 40)])
    print(pu1)
    print("Validation pompe:", pu1.validate_flowcad())
    #Créer une valve
    v1 = Valve("V1", start_node="J3", end_node="J4", diameter=0.2, valve_type='PRV', setting=30.0)
    print(v1)
    print("Validation valve:", v1.validate_flowcad())   
    #Créer une valve avec erreur
    v2 = Valve("V2", start_node="J4", end_node="J5", diameter=-0.2, valve_type='XYZ', setting=30.0)
    print(v2)   
    print("Validation valve avec erreur:", v2.validate_flowcad())   