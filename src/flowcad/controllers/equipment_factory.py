from typing import Dict, Any
import math
from ..models.equipment import equipment_classes
from ..models.equipment.base_equipment import BaseEquipment
from ..core.unit_manager import UnitManager, PressureUnit, FlowUnit
from ..models import hydraulic_converter as hc


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
            elif equipment_type in ["V1", "Vb"]:  #il s'agit d'une vanne
                check_valve = False
                opening_status = properties.get('opening_value', 100)
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
        elif equipment_class.__name__ == 'FlowRateBoundaryConditionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('flow_rate_m3s', 0.1),
                properties.get('elevation', 0.0)
            )
        elif equipment_class.__name__ == 'TeeConnectionEquipment':
            return equipment_class(
                equipment_id,
                properties.get('diameter_m', 1.0),
                properties.get('elevation', 0.0)
            )
        #---------------------------------------------------------------------------------------
        #si l'équipement est une vanne -------------------------------------------------------
        elif equipment_class.__name__ == 'ValveEquipment':

            #Vanne de type vanne 2 voies, progressive (TCV) if equipment_type == "V2V_p"
            print(f"type d'équipement: {equipment_type}")
            opening_value = properties.get('opening_value', 100)
            
            valve_control_type = properties.get('valve_control_type', 'linear')
            #Le zeta de la vanne 100% ouverte, à partir du kv_s
            zeta = hc.HydraulicConverter.zeta_from_kv(
                kv=properties.get('kv_s', 1.0),
                diameter=properties.get('diameter_m', 0.1)
            )
            #print(f"opening_value dans EquipmentFactory: {opening_value}, zeta calculé: {zeta}", "kv=", properties.get('kv_s', 1.0))
            #le kv effectif en fonction de l'ouverture et du type de contrôle
            if valve_control_type == 'linear':
                opening_value = float(opening_value)
                if opening_value < 0 or opening_value > 100:
                    raise ValueError("La valeur d'ouverture doit être entre 0 et 100")
                opening_value = max(0.0, min(100.0, opening_value))  # Clamp entre 0 et 100
                if opening_value == 0:
                    status = 'CLOSED'
                elif opening_value == 100:
                    status = 'OPEN'
                else:
                    status = 'ACTIVE'
                #relation linéaire entre l'ouverture et le kv effectif
                kv_eff = properties.get('kv_s', 1.0) * (opening_value) / 100
            elif valve_control_type == 'equal_percentage':
                opening_value = float(opening_value)
                if opening_value < 0 or opening_value > 100:
                    raise ValueError("La valeur d'ouverture doit être entre 0 et 100")
                opening_value = max(0.0, min(100.0, opening_value))  # Clamp entre 0 et 100
                if opening_value == 0:
                    status = 'CLOSED'
                elif opening_value == 100:
                    status = 'OPEN'
                else:
                    status = 'ACTIVE'
                #relation exponentielle entre l'ouverture et le kv effectif
                n=3 #exposant
                relative_opening = opening_value / 100
                kv_s = properties.get('kv_s', 1.0)
                relative_opening_switch = 0.4
                e = math.e
                relative_kv_switch = e**(n * (relative_opening_switch - 1))
                print(f"relative_kv_switch dans EquipmentFactory: {relative_kv_switch}, relative_opening switch: {relative_opening_switch} relative_opening: {relative_opening}")
                if relative_opening < relative_opening_switch:
                    kv_eff = kv_s * (relative_opening / relative_opening_switch) * relative_kv_switch
                else:
                    kv_eff = e**(n * (relative_opening - 1)) * kv_s
            elif valve_control_type == 'binary':  #une vanne qui ne peut être que ouverte ou fermée
                opening_value = float(opening_value)
                print(f"valeur d'ouverture: {opening_value}")
                kv_eff = properties.get('kv_s', 1.0)
                zeta = hc.HydraulicConverter.zeta_from_kv(
                kv=kv_eff,
                diameter=properties.get('diameter_m', 0.1)
                )
                if opening_value < 50:
                    status = 'CLOSED'
                else: 
                    status = 'OPEN'
            else:
                raise ValueError(f"Type de contrôle de vanne inconnu: {valve_control_type}")
            
            zeta_active = hc.HydraulicConverter.zeta_from_kv(
                kv=kv_eff,
                diameter=properties.get('diameter_m', 0.1)
            )
            print(f"zeta_active calculé dans EquipmentFactory: {zeta_active}")

            return equipment_class(
                id=equipment_id,
                diameter=properties.get('diameter_m', 0.1),
                zeta=zeta,
                elevation=properties.get('elevation', 0.0),
                valve_type='TCV',
                initial_status=status,
                setting=zeta_active
            )
        #---------------------------------------------------------------------------------------
        #si l'équipement est une vanne 3V-------------------------------------------------------
        elif equipment_class.__name__ == 'ThreeWayValveEquipment':

            #Vanne de type vanne 3 voies, progressive (TCV) if equipment_type == "V3V_p"
            print(f"type d'équipement: {equipment_type}")
            opening_value = properties.get('opening_value', 100)
            
            valve_control_type = properties.get('valve_control_type', 'linear')
            #Le zeta de la vanne 100% ouverte, à partir du kv_s
            zeta = hc.HydraulicConverter.zeta_from_kv(
                kv=properties.get('kv_s', 1.0),
                diameter=properties.get('diameter_m', 0.1)
            )
            #print(f"opening_value dans EquipmentFactory: {opening_value}, zeta calculé: {zeta}", "kv=", properties.get('kv_s', 1.0))
            #le kv effectif en fonction de l'ouverture et du type de contrôle
            if valve_control_type == 'linear':
                opening_value = float(opening_value)
                if opening_value < 0 or opening_value > 100:
                    raise ValueError("La valeur d'ouverture doit être entre 0 et 100")
                opening_value = max(0.0, min(100.0, opening_value))  # Clamp entre 0 et 100
                if opening_value == 0:
                    status_1 = 'CLOSED'
                    status_2 = 'OPEN'
                elif opening_value == 100:
                    status_1 = 'OPEN'
                    status_2 = 'CLOSED'
                else:
                    status_1 = 'ACTIVE'
                    status_2 = 'ACTIVE'
                #relation linéaire entre l'ouverture et le kv effectif
                kv_eff_1 = properties.get('kv_s', 1.0) * (opening_value) / 100
                kv_eff_2 = properties.get('kv_s', 1.0) * (100 - opening_value) / 100
            elif valve_control_type == 'equal_percentage':
                pass
                '''opening_value = float(opening_value)
                if opening_value < 0 or opening_value > 100:
                    raise ValueError("La valeur d'ouverture doit être entre 0 et 100")
                opening_value = max(0.0, min(100.0, opening_value))  # Clamp entre 0 et 100
                if opening_value == 0:
                    status = 'CLOSED'
                elif opening_value == 100:
                    status = 'OPEN'
                else:
                    status = 'ACTIVE'
                #relation exponentielle entre l'ouverture et le kv effectif
                n=3 #exposant
                relative_opening = opening_value / 100
                kv_s = properties.get('kv_s', 1.0)
                relative_opening_switch = 0.4
                e = math.e
                relative_kv_switch = e**(n * (relative_opening_switch - 1))
                print(f"relative_kv_switch dans EquipmentFactory: {relative_kv_switch}, relative_opening switch: {relative_opening_switch} relative_opening: {relative_opening}")
                if relative_opening < relative_opening_switch:
                    kv_eff = kv_s * (relative_opening / relative_opening_switch) * relative_kv_switch
                else:
                    kv_eff = e**(n * (relative_opening - 1)) * kv_s'''

            else:
                raise ValueError(f"Type de contrôle de vanne inconnu: {valve_control_type}")
            
            zeta_active_1 = hc.HydraulicConverter.zeta_from_kv(
                kv=kv_eff_1,
                diameter=properties.get('diameter_m', 0.1)
            )
            zeta_active_2 = hc.HydraulicConverter.zeta_from_kv(
                kv=kv_eff_2,
                diameter=properties.get('diameter_m', 0.1)
            )
            print(f"zeta_active_1 calculé dans EquipmentFactory: {zeta_active_1}")
            print(f"zeta_active_2 calculé dans EquipmentFactory: {zeta_active_2 }")

            return equipment_class(
                id=equipment_id,
                diameter=properties.get('diameter_m', 0.1),
                zeta=zeta,
                elevation=properties.get('elevation', 0.0),
                valve_type='TCV',
                initial_status_1=status_1,
                initial_status_2=status_2,
                setting_1=zeta_active_1,
                setting_2=zeta_active_2
            )
        # Ajouter d'autres types au fur et à mesure...
        else:
            raise NotImplementedError(f"Création non implémentée pour {equipment_class.__name__}")