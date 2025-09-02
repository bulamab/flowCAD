"""
Classe simple pour charger la configuration des équipements depuis JSON
"""
import json
import os
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
    
    #fonction qui retourne la liste des équipements pour une catégorie
    def get_equipment_items_for_category(self, category_data: Dict[str, any]) -> List[str]:

        return category_data.get('equipment_items', [])
    
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