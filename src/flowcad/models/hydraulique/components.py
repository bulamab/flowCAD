"""
src/flowcad/models/hydraulique/components.py

Classe de base pour tous les composants hydrauliques FlowCAD
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class HydraulicComponent(ABC):
    """
    Classe de base abstraite pour tous les composants hydrauliques.
    
    Cette classe définit l'interface commune pour tous les composants
    qui peuvent être simulés avec WNTR (jonctions, réservoirs, tuyaux, pompes, etc.)
    """
    
    def __init__(self, component_id: str):
        """
        Constructeur de base pour un composant hydraulique.
        
        Args:
            component_id (str): Identifiant unique du composant
            
        Raises:
            ValueError: Si l'ID est vide ou None
        """
        if not component_id or not isinstance(component_id, str):
            raise ValueError("L'ID du composant doit être une chaîne non vide")
        
        self.id = component_id.strip()
        if not self.id:
            raise ValueError("L'ID du composant ne peut pas être vide")
            
        self.is_active = True
        self.metadata: Dict[str, Any] = {}
    

    @abstractmethod
    def to_wntr(self, wn_network):
        """
        Convertit ce composant vers le format WNTR.
        
        Cette méthode doit être implémentée par chaque composant spécialisé
        pour ajouter le composant correspondant au réseau WNTR.
        
        Args:
            wn_network: Instance de wntr.network.WaterNetworkModel
            
        Raises:
            NotImplementedError: Si la méthode n'est pas implémentée
        """
        pass
    
    def validate_flowcad(self) -> List[str]:
        """
        Valide le composant selon les règles FlowCAD.
        
        Cette méthode peut être surchargée par les classes dérivées
        pour ajouter des validations spécifiques.
        
        Returns:
            List[str]: Liste des erreurs de validation (vide si valide)
        """
        errors = []
        
        if not self.id:
            errors.append("ID du composant manquant")
            
        return errors
    
    def __str__(self) -> str:
        """Représentation textuelle du composant"""
        return f"{self.__class__.__name__}(id='{self.id}')"
    
    def __repr__(self) -> str:
        """Représentation pour debug"""
        return f"{self.__class__.__name__}(id='{self.id}', active={self.is_active})"


class HydraulicNode(HydraulicComponent):
    """
    Classe de base pour les nœuds hydrauliques (jonctions, réservoirs).
    """
    
    def __init__(self, component_id: str, elevation: float = 0.0):
        super().__init__(component_id)
        self.elevation = elevation  # en mètres
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not isinstance(self.elevation, (int, float)):
            errors.append("L'élévation doit être un nombre")
        
        return errors
    
    def to_wntr(self, wn_network):
        return super().to_wntr(wn_network)  # Appel de la méthode abstraite 
    
class HydraulicLink(HydraulicComponent):
    """
    Classe de base pour les liens hydrauliques (tuyaux, pompes).
    """
    
    def __init__(self, component_id: str, start_node: str, end_node: str):
        super().__init__(component_id)
        self.start_node = start_node
        self.end_node = end_node
    
    def validate_flowcad(self) -> List[str]:
        errors = super().validate_flowcad()
        
        if not self.start_node or not isinstance(self.start_node, str):
            errors.append("Le nœud de départ doit être une chaîne non vide")
        
        if not self.end_node or not isinstance(self.end_node, str):
            errors.append("Le nœud d'arrivée doit être une chaîne non vide")
        
        if self.start_node == self.end_node:
            errors.append("Le nœud de départ et d'arrivée ne peuvent pas être identiques")
        
        return errors
    
    def to_wntr(self, wn_network):
        return super().to_wntr(wn_network)  # Appel de la méthode abstraite 



# Test simple de la classe
if __name__ == "__main__":
    # Cette partie ne sera exécutée que si on lance ce fichier directement
    
    # Test basique - ne peut pas être instanciée car abstraite
    try:
        # Ceci devrait lever une erreur
        comp = HydraulicComponent("test")
        print("❌ Erreur: La classe abstraite a été instanciée")
    except TypeError as e:
        print("✅ Classe abstraite correctement implémentée:", str(e))
    
    # Test avec classe concrète minimale pour démonstration
    class TestComponent(HydraulicComponent):
        def to_wntr(self, wn_network):
            print(f"Conversion {self.id} vers WNTR")
    
    # Tests de validation
    print("\n--- Tests de validation ---")
    
    # Test ID valide
    test_comp = TestComponent("COMP_001")
    print(f"Composant créé: {test_comp}")
    errors = test_comp.validate_flowcad()
    print(f"Erreurs de validation: {errors}")


    #Test hydraulic node
    print("\n--- Test HydraulicNode ---")
    node = HydraulicNode("NODE_001", elevation=15.0)
    print(f"Composant créé: {node}")
    errors = node.validate_flowcad()    
    print(f"Erreurs de validation: {errors}")

    #Test hydraulic link
    print("\n--- Test HydraulicLink ---")
    link = HydraulicLink("LINK_001", start_node="NODE_001", end_node="NODE_002")
    print(f"Composant créé: {link}")
    errors = link.validate_flowcad()    
    print(f"Erreurs de validation: {errors}") 
    
    # Test ID invalide
    try:
        invalid_comp = TestComponent(" ")
        print("❌ Erreur: ID vide accepté")
    except ValueError as e:
        print(f"✅ ID vide rejeté: {e}")
    
    try:
        invalid_comp = TestComponent(None)
        print("❌ Erreur: ID None accepté")
    except ValueError as e:
        print(f"✅ ID None rejeté: {e}")