"""
Module centralisé pour toutes les classes d'équipements
"""

# Import de toutes les classes depuis les différents modules
from .active_equipment import (
    PumpEquipment,
    PressureBoundaryConditionEquipment,
    FlowRateBoundaryConditionEquipment,
    HydraulicResistanceEquipment,
    ValveEquipment
)

from .connections import (
    PipeConnectionEquipment,
    TeeConnectionEquipment
)

# Vous pouvez ajouter d'autres imports si nécessaire
# from .infrastructure_equipment import ...

# Export explicite (optionnel mais recommandé)
__all__ = [
    'PumpEquipment',
    'PressureBoundaryConditionEquipment', 
    'FlowRateBoundaryConditionEquipment',
    'HydraulicResistanceEquipment',
    'PipeConnectionEquipment',
    'TeeConnectionEquipment',
    'ValveEquipment'
]