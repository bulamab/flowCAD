from typing import Dict, Any
from ..models.equipment import equipment_classes
from ..models.equipment.base_equipment import BaseEquipment
from ..models.equipment.connections import PipeConnectionEquipment


class PipeFactory:
    """Crée les tuyaux depuis les définitions GUI"""

    @staticmethod
    def create_from_gui_polyline(gui_polyline) -> BaseEquipment:
        """
        Crée un tuyau métier depuis un PolylineGraphicsItem

        Args:
            gui_polyline: Instance de PolylineGraphicsItem
            
        Returns:
            Instance de BaseEquipment, dans le cas présent PipeConnectionEquipment(BaseEquipment):
        """
        pipe_def = gui_polyline.pipe_def
        properties = pipe_def.get('properties', {})
        
        
        # Création avec adaptation des paramètres
        return PipeConnectionEquipment(
            gui_polyline.pipe_id,
            properties.get('length_m', 1.0),
            properties.get('diameter_m', 0.1),
            properties.get('roughness_mm', 0.1)
        )
    
    '''@staticmethod
    def _create_instance(pipe_id: str, properties: Dict[str, Any]) -> BaseEquipment:
        """Adapte les paramètres selon le type d'équipement"""
        
        # Mapping des propriétés selon le type (à adapter selon vos besoins)
        if equipment_class.__name__ == 'PumpEquipment':
            curve_points = [(properties.get('flow_rate_1', 40), properties.get('pressure_1', 10))]
            elevation = properties.get('elevation', 0.0)
            return equipment_class(equipment_id, curve_points, elevation)
            
        elif equipment_class.__name__ == 'PipeConnectionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('length_m', 1.0),
                properties.get('diameter_m', 0.1),
                properties.get('roughness_mm', 0.1)
            )
            
        elif equipment_class.__name__ == 'PressureBoundaryConditionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('pressure_bar', 1.0),
                properties.get('elevation', 0.0)
            )
            
        # Ajouter d'autres types au fur et à mesure...
        else:
            raise NotImplementedError(f"Création non implémentée pour {equipment_class.__name__}")'''