"""
Classe simple pour charger la configuration des équipements depuis JSON
"""
import json
import os
import importlib
from typing import Dict, Any, List

from pathlib import Path

class EquipmentLoader:
    def __init__(self):
        # Trouver le fichier de config (à adapter selon votre structure)
        current_dir = Path(__file__).resolve().parent
        self.config_file = current_dir / 'equipment_config.json'
        self.resources_dir = current_dir.parent/ 'resources'  # Dossier pour les SVG
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """Charge le fichier JSON de configuration"""
        if self._config is None:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except FileNotFoundError:
                print(f"Fichier de config non trouvé: {self.config_file}")
                self._config = {"equipment_categories": {}, "equipment_definitions": {}}
            except json.JSONDecodeError as e:
                print(f"Erreur JSON: {e}")
                self._config = {"equipment_categories": {}, "equipment_definitions": {}}
        return self._config
    
    def get_categories(self) -> Dict[str, Any]:
        """Retourne la structure des catégories"""
        config = self.load_config()
        return config.get('equipment_categories', {})
    
    def get_equipment_definitions(self) -> Dict[str, Any]:
        """Retourne la définition des équipements"""
        config = self.load_config()
        return config.get('equipment_definitions', {})
    
    def get_single_equipment_definition(self, equipment_id: str) -> Dict[str, Any]:
        """Retourne la définition d'un équipement spécifique"""
        definitions = self.get_equipment_definitions()
        return definitions.get(equipment_id, {})
    
    def get_single_equipment_properties(self, equipment_id: str) ->  Dict[str, Any]:
        """Retourne une propriété spécifique d'un équipement"""
        definition = self.get_single_equipment_definition(equipment_id)
        return definition.get('properties', {})

    #Fonction qui retourne le nom de la classe d'un équipement
    def get_equipment_class_name(self, equipment_id: str) -> str:
        """Retourne la classe d'un équipement spécifique"""
        definition = self.get_single_equipment_definition(equipment_id)
        return definition.get('equipment_class', 'BaseEquipment')
    
    #Fonction qui crée une instanance de la classe d'un équipement
    def create_equipment_instance(self, equipment_id: str, **kwargs) -> Any:
        """Factory method pour créer une instance d'équipement"""
        class_name = self.get_equipment_class_name(equipment_id)
        # Import dynamique du module contenant les classes d'équipements
        # Adaptez le nom du module selon votre structure
        try:
            equipment_module = importlib.import_module('src.flowcad.models.equipment.equipment_classes')
            equipment_class = getattr(equipment_module, class_name)
            
            # Récupérer les propriétés par défaut
            default_properties = self.get_single_equipment_properties(equipment_id)
            print(f"🔍 Création de {class_name} avec propriétés: {default_properties}")

            # Créer l'instance
            return equipment_class(id=equipment_id, **default_properties)

        except (ImportError, AttributeError) as e:
            print(f"Erreur lors de la création de {class_name}: {e}")
            # Fallback sur BaseEquipment
            from src.flowcad.models.equipment import BaseEquipment
            return BaseEquipment(id=equipment_id, **kwargs)

    #Fonction qui retourne le chemin complet vers le fichier SVG d'un équipement
    def get_svg_path(self, equipment_id: str) -> str:
        """Retourne le chemin complet vers le fichier SVG"""
        definition = self.get_single_equipment_definition(equipment_id)
        icon_svg = definition.get('icon_svg', '')
        
        if icon_svg:
            svg_path = self.resources_dir /  icon_svg
            return str(svg_path)
        else:
            # Fichier SVG par défaut si non trouvé
            default_path = self.resources_dir /  'default.svg'
            return str(default_path)

# Test de fonction
if __name__ == "__main__": 
    loader = EquipmentLoader()
    categories = loader.get_categories()
    definitions = loader.get_equipment_definitions()
    print("Catégories:", json.dumps(categories, indent=2, ensure_ascii=False))
    print("Définitions:", json.dumps(definitions, indent=2, ensure_ascii=False))
    print("Équipement spécifique:", json.dumps(loader.get_single_equipment_definition("pompe_simple"), indent=2, ensure_ascii=False))
    print("Chemin SVG:", loader.get_svg_path("pompe_simple"))
    print("Propriétés spécifiques:", json.dumps(loader.get_single_equipment_properties("pompe_simple"), indent=2, ensure_ascii=False))
    test = loader.create_equipment_instance("pompe_simple")
    print("Instance d'équipement créée:", test)