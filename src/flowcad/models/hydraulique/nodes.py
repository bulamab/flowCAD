try:
    from .components import HydraulicComponent, HydraulicNode
except ImportError:
    from components import HydraulicComponent, HydraulicNode




from typing import List


class Junction(HydraulicNode):
    """
    Classe représentant une jonction hydraulique.
    """
    
    def __init__(self, component_id: str, elevation: float = 0.0, demand: float = 0.0):
        super().__init__(component_id, elevation)
        self.demand = demand  # en m³/s
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.demand, (int, float)):
            errors.append("La demande doit être un nombre")
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_junction(
            name=self.id,
            base_demand=self.demand,
            elevation=self.elevation
        )
        return wn_network.get_node(self.id)
    
class Reservoir(HydraulicNode):
    """
    Classe représentant un réservoir hydraulique.
    """
    
    def __init__(self, component_id: str, elevation: float = 0.0, head: float = 0.0):
        super().__init__(component_id, elevation)
        self.head = head  # en mètres
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.head, (int, float)):
            errors.append("La hauteur doit être un nombre")
        
        return errors
    
    def to_wntr(self, wn_network):
        wn_network.add_reservoir(
            name=self.id,
            base_head=self.head
        )
        return wn_network.get_node(self.id)
    
class tank(HydraulicNode):
    """
    Classe représentant un réservoir (tank) hydraulique.
    """
    
    def __init__(self, component_id: str, elevation: float = 0.0, init_level: float = 0.0, min_level: float = 0.0, max_level: float = 10.0, diameter: float = 1.0):
        super().__init__(component_id, elevation)
        self.init_level = init_level  # en mètres
        self.min_level = min_level    # en mètres   
        self.max_level = max_level    # en mètres
        self.diameter = diameter      # en mètres

    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.init_level, (int, float)):
            errors.append("Le niveau initial doit être un nombre")
            
            if not isinstance(self.min_level, (int, float)):
                errors.append("Le niveau minimum doit être un nombre")
            
            if not isinstance(self.max_level, (int, float)):
                errors.append("Le niveau maximum doit être un nombre")
            
            if not isinstance(self.diameter, (int, float)) or self.diameter <= 0:
                errors.append("Le diamètre doit être un nombre positif")
            
            if self.min_level >= self.max_level:
                errors.append("Le niveau minimum doit être inférieur au niveau maximum")
            
            if not (self.min_level <= self.init_level <= self.max_level):
                errors.append("Le niveau initial doit être entre le niveau minimum et maximum")
            
            return errors
        
        def to_wntr(self, wn_network):
            wn_network.add_tank(
                name=self.id,
                elevation=self.elevation,
                init_level=self.init_level,
                min_level=self.min_level,
                max_level=self.max_level,
                diameter=self.diameter
            )
            return wn_network.get_node(self.id)
        
    
    #Test simple de la classe Reservoir

#Test fonctionnement des noeuds------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Créer une jonction
    j1 = Junction("J1", elevation=10.0, demand=0.01)
    print(j1)
    print("Validation jonction:", j1.validate_flowcad())
    
    # Créer un réservoir
    r1 = Reservoir("R1", elevation=20.0, head=50.0)
    print(r1)
    print("Validation réservoir:", r1.validate_flowcad())

    # Créer un tank
    t1 = tank("T1", elevation=15.0, init_level=5.0, min_level=1.0, max_level=10.0, diameter=3.0)
    print(t1)  
    print("Validation tank:", t1.validate_flowcad())
    
    # Test ID invalide
    try:
        invalid_junction = Junction(" ")
        print("❌ Erreur: ID vide accepté")
    except ValueError as e:
        print(f"✅ ID vide rejeté: {e}")
    
    try:
        invalid_reservoir = Reservoir("")
        print("❌ Erreur: ID vide accepté")
    except ValueError as e:
        print(f"✅ ID vide rejeté: {e}")
