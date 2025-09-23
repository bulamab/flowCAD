from typing import Dict, Any
from ..models.equipment import equipment_classes
from ..models.equipment.base_equipment import BaseEquipment
from ..core.unit_manager import UnitManager, PressureUnit, FlowUnit


class EquipmentFactory:
    """Crée des équipements métier depuis les définitions GUI"""

    @staticmethod
    def create_from_gui_item(gui_item) -> BaseEquipment:
        """
        Crée un équipement métier depuis un EquipmentGraphicsItem
        
        Args:
            gui_item: Instance d'EquipmentGraphicsItem
            
        Returns:
            Instance de BaseEquipment (PumpEquipment, PipeConnectionEquipment, etc.)
        """
        equipment_def = gui_item.equipment_def
        equipment_class_name = equipment_def.get('equipment_class')
        properties = equipment_def.get('properties', {})
        equipment_type = gui_item.equipment_type
        
        # Récupération dynamique de la classe
        if hasattr(equipment_classes, equipment_class_name):
            equipment_class = getattr(equipment_classes, equipment_class_name)
        else:
            raise ValueError(f"Classe d'équipement inconnue: {equipment_class_name}")
        
        # Création avec adaptation des paramètres
        return EquipmentFactory._create_instance(
            equipment_class, 
            gui_item.equipment_id, 
            properties,
            equipment_type
        )
    
    @staticmethod
    def _create_instance(equipment_class, equipment_id: str, properties: Dict[str, Any], equipment_type: str) -> BaseEquipment:
        """Adapte les paramètres selon le type d'équipement"""
        
        # Mapping des propriétés selon le type (à adapter selon vos besoins)
        if equipment_class.__name__ == 'PumpEquipment':
            #curve_points = [(properties.get('flow_rate_1', 40), properties.get('pressure_1', 10))]
            curve_points = properties.get('curve_points', [(40, 10)])
            #convertit les points de la courbe en m3/s et mCE
            converted_points = [(q, p/ (1000 * 9.81)) for (q, p) in curve_points]
            elevation = properties.get('elevation', 0.0)
            return equipment_class(equipment_id, converted_points, elevation)

        elif equipment_class.__name__ == 'HydraulicResistanceEquipment':
            print(f"type d'équipement: {equipment_type}")
            if equipment_type == "CAR":  #il s'agit d'un clapet anti-retour
                check_valve = True #variable qui définit si l'équipement est un clapet anti-retour
                initial_status = 'OPEN'  #par défaut, le clapet est ouvert
            elif equipment_type == "V1":  #il s'agit d'une vanne
                check_valve = False
                opening_status = properties.get('opening_status', 100)
                print(f"opening_status dans EquipmentFactory: {opening_status}")
                if float(opening_status) >= 50:
                    initial_status = 'OPEN'
                else:
                    initial_status = 'CLOSED'
            else:
                check_valve = False

            return equipment_class(
                equipment_id,
                properties.get('diameter_m', 1.0),
                properties.get('zeta', 0.1),
                properties.get('elevation', 0),
                check_valve=check_valve,
                initial_status=initial_status
            )
            
        elif equipment_class.__name__ == 'PressureBoundaryConditionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('pressure_bar', 1.0),
                properties.get('elevation', 0.0)
            )
        elif equipment_class.__name__ == 'TeeConnectionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('diameter_m', 1.0),
                properties.get('elevation', 0.0)
            )

        # Ajouter d'autres types au fur et à mesure...
        else:
            raise NotImplementedError(f"Création non implémentée pour {equipment_class.__name__}")