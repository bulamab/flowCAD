from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..hydraulique.components import HydraulicComponent

#classe de base pour tous les ports d'un équipement---------------------------------------------------------------------------------

class Port:
    """
    Classe représentant un port de connexion pour les équipements.
    
    Un port peut être un point d'entrée ou de sortie pour les flux hydrauliques.
    """
    
    def __init__(self, port_id: str, parent_equipment_id: str):
        """
        Constructeur de base pour un port.
        
        Args:
            port_id (str): Identifiant unique du port
            parent_equipment_id (str): ID de l'équipement parent auquel ce port appartient
            
        Raises:
            ValueError: Si l'ID et le parent ID sont vides
    
        """
        if not port_id or not isinstance(port_id, str):
            raise ValueError("L'ID du port doit être une chaîne non vide")
        
        self.id = port_id.strip()
        if not self.id:
            raise ValueError("L'ID du port ne peut pas être vide")
        
        if parent_equipment_id is None or not isinstance(parent_equipment_id, str):
            raise ValueError("L'ID de l'équipement parent doit être une chaîne non vide")
        
        self.parent_equipment_id = parent_equipment_id.strip()
        if not self.parent_equipment_id:
            raise ValueError("L'ID de l'équipement parent ne peut pas être vide")
        
        #Etat du port (connecté ou non)
        self.is_connected = False
        self.connected_to_equipment: Optional[str] = None  # ID de l'équipement connecté, None si non connecté
        self.connected_to_port: Optional[str] = None  # ID du port connecté, None si non connecté

    #Methodes de connexion/déconnexion du port =================================================================================

    #Methode pour connecter ce port à un autre équipement
    def connect(self, other_equipment_id: str, other_port_id: str):

        #vérifier que le port n'est pas déjà connecté
        if self.is_connected:
            raise ValueError(f"Le port '{self.id}' de l'équipement '{self.parent_equipment_id}' est déjà connecté à '{self.connected_to}'")

        #verifier que l'ID de l'autre équipement est valide
        if not other_equipment_id or not isinstance(other_equipment_id, str):
            raise ValueError("L'ID de l'équipement connecté doit être une chaîne non vide")
        
        #verifier que l'autre port ID est valide
        if not other_port_id or not isinstance(other_port_id, str):
            raise ValueError("L'ID du port auquel il faut se connecter doit être une chaîne non vide")
        
        #vérifier que l'on ne se connecte pas à soi-même
        if self.parent_equipment_id == other_equipment_id.strip() and self.id == other_port_id.strip():
            raise ValueError("Un port ne peut pas se connecter à lui-même")
        
        #vérifier que le port de l'autre équipement est déconnecté
        #ne peut pas être vérifié ici, doit être géré par le gestionnaire de réseau
        
        #connecter le port
        self.is_connected = True
        self.connected_to_equipment = other_equipment_id.strip()
        if not self.connected_to_equipment:
            raise ValueError("L'ID de l'équipement connecté ne peut pas être vide")
        self.connected_to_port = other_port_id.strip()
        if not self.connected_to_port:
            raise ValueError("L'ID du port connecté ne peut pas être vide")
        
    #Methode pour déconnecter ce port
    def disconnect(self):
        self.is_connected = False
        self.connected_to_equipment = None
        self

    #Metodes d'état du port ============================================================================================
    
    #Methode pour vérifier si le port est connecté
    def is_port_connected(self) -> bool:
        return self.is_connected
    
    #methodes d'accès aux informations de connexion =================================================================================

    #Methode pour obtenir l'ID de l'équipement connecté (ou None si non connecté)
    def get_connected_equipment(self) -> Optional[str]:
        return self.connected_to_equipment
    
    #Methode pour obtenir l'ID du port connecté (ou None si non connecté)
    def get_connected_port(self) -> Optional[str]:
        return self.connected_to_port
    
    #methode pour obtenir l'ID du parent equipment
    def get_parent_equipment_ID(self) -> str:
        return self.parent_equipment_id
    
    #metode pour  obtenir toutes les informations du port 
    def get_port_info(self) -> Dict[str, Any]:
        return {
            "port_id": self.id,
            "parent_equipment_id": self.parent_equipment_id,
            "is_connected": self.is_connected,
            "connected_to_equipment": self.connected_to_equipment,
            "connected_to_port": self.connected_to_port
        }
    
    #méthodes de validation ============================================================================================
    def validate(self) -> List[str]:
        errors = []
        
        if not self.id:
            errors.append("ID du port manquant")
        
        if not self.parent_equipment_id:
            errors.append("ID de l'équipement parent manquant")
        
        if self.is_connected:
            if not self.connected_to_equipment:
                errors.append("Le port est marqué comme connecté mais l'ID de l'équipement connecté est manquant")
            if not self.connected_to_port:
                errors.append("Le port est marqué comme connecté mais l'ID du port connecté est manquant")
        
        return errors
    
    #Représentation textuelle du port ============================================================================================
    def __str__(self) -> str:
        status = "connecté" if self.is_connected else "déconnecté"
        connected_info = f" à {self.connected_to_equipment}.{self.connected_to_port}" if self.is_connected else ""
        return f"Port(id='{self.id}', parent_equipment_id='{self.parent_equipment_id}', status='{status}'{connected_info})"

#========================================================================================================================
#Classe de base pour tous les équipements---------------------------------------------------------------------------------
#========================================================================================================================

class BaseEquipment(ABC):
    """
    Classe de base abstraite pour tous les équipements.
    
    Cette classe définit l'interface et les fonctionnalités communes 
    à tous les équipements hydrauliques.
    """
    
    def __init__(self, equipment_id: str):
        """
        Constructeur de base pour un équipement.
        
        Args:
            equipment_id (str): Identifiant unique de l'équipement
            
        Raises:
            ValueError: Si l'ID est vide
        """
        if not equipment_id or not isinstance(equipment_id, str):
            raise ValueError("L'ID de l'équipement doit être une chaîne non vide")
        
        self.id = equipment_id.strip()
        if not self.id:
            raise ValueError("L'ID de l'équipement ne peut pas être vide")
        
        self.ports: Dict[str, Port] = {}  # Dictionnaire des ports par ID

    #Méthodes de gestion des ports ============================================================================================
    
    #Methode pour ajouter un port à l'équipement
    def add_port(self, port: Port):
        if not isinstance(port, Port):
            raise ValueError("Le port doit être une instance de la classe Port")
        
        if port.id in self.ports:
            raise ValueError(f"Un port avec l'ID '{port.id}' existe déjà dans l'équipement '{self.id}'")
        
        if port.parent_equipment_id != self.id:
            raise ValueError(f"L'ID de l'équipement parent du port '{port.parent_equipment_id}' ne correspond pas à l'ID de l'équipement '{self.id}'")
        
        self.ports[port.id] = port
    
    #Methode pour obtenir un port par son ID
    def get_port(self, port_id: str) -> Optional[Port]:
        return self.ports.get(port_id)
    
    #Methode pour obtenir tous les ports
    def get_all_ports(self) -> List[Port]:
        return list(self.ports.values())
    
    #Méthodes d'accès aux informations de l'équipement ============================================================================================
    
    #Methode pour obtenir l'ID de l'équipement
    def get_equipment_ID(self) -> str:
        return self.id
    
    #Méthode pour obtenir les informations complètes de l'équipement
    def get_equipment_info(self) -> Dict[str, Any]:
        return {
            "equipment_id": self.id,   
            "ports": [port.get_port_info() for port in self.get_all_ports()]
        }
    
    #Methode pour verifier si l'équipement est complètement connecté (tous les ports connectés)
    def is_fully_connected(self) -> bool:
        return all(port.is_port_connected() for port in self.get_all_ports())
    
    #methode abstraite pour générer la représentation hydraulique de l'équipement ================================================================================
    @abstractmethod
    def generate_hydraulic_representation(self) -> List[HydraulicComponent]:
        """
        Méthode abstraite pour générer la représentation hydraulique de l'équipement.
        
        Doit être implémentée par les classes dérivées.
        """
        pass

    #méthodes de validation ============================================================================================
    def validate(self) -> List[str]:
        errors = []
        
        #vérifier que l'ID de l'équipement est défini
        if not self.id:
            errors.append("ID de l'équipement manquant")
        
        #vérifier qu'il y a au moins un port
        if not self.ports:
            errors.append(f"L'équipement '{self.id}' n'a pas de ports définis")
        
        #valider chaque port
        for port in self.get_all_ports():
            port_errors = port.validate()
            if port_errors:
                errors.extend([f"Port '{port.id}' de l'équipement '{self.id}': {err}" for err in port_errors])

        #verifier que tous les ports appartiennent à cet équipement   
        for port in self.get_all_ports():
            if port.parent_equipment_id != self.id:
                errors.append(f"Le port '{port.id}' appartient à l'équipement '{port.parent_equipment_id}' au lieu de '{self.id}'")

        #vérifier que les ports ont des IDs uniques
        port_ids = [port.id for port in self.get_all_ports()] 
        if len(port_ids) != len(set(port_ids)):
            errors.append(f"L'équipement '{self.id}' a des ports avec des IDs dupliqués") 

        return errors




#test simple de la classe Port---------------------------------------------------------------------------------
if __name__ == "__main__":
    #Créer un port
    p1 = Port("P1", "E1")
    print(p1)
    
    #Valider le port
    print("Validation port:", p1.validate())
    
    #Connecter le port à un autre équipement
    p1.connect("E2", "P2")
    print(p1)
    
    #Valider le port après connexion
    print("Validation port après connexion:", p1.validate())
    
    #Déconnecter le port
    p1.disconnect()
    print(p1)
    
    #Valider le port après déconnexion
    print("Validation port après déconnexion:", p1.validate())

