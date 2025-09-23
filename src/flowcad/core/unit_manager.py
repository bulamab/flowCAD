from enum import Enum
from typing import Dict, Any, Optional
import json

class PressureUnit(Enum):
    """Énumération des unités de pression disponibles"""
    BAR = "bar"
    KPA = "kPa"
    PA = "Pa"
    MCE = "mCE"  # mètres colonne d'eau

class FlowUnit(Enum):
    """Énumération des unités de débit disponibles"""
    M3_S = "m³/s"
    M3_H = "m³/h"
    L_S = "L/s"
    L_MIN = "L/min"
    L_H = "L/h"

class UnitManager:
    """
    Gestionnaire des unités pour l'AFFICHAGE des résultats hydrauliques.
    Pattern Singleton pour garantir une seule instance dans toute l'application.
    
    PRINCIPE: 
    - Les objets stockent toujours les valeurs en unités SI (Pa, m³/s, m)
    - La conversion se fait uniquement lors de l'affichage
    - Une seule instance partagée dans toute l'application
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Pattern Singleton : une seule instance"""
        if cls._instance is None:
            cls._instance = super(UnitManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisation une seule fois grâce au flag _initialized"""
        if UnitManager._initialized:
            return
            
        # Unités par défaut pour l'affichage
        self.pressure_unit = PressureUnit.KPA
        self.flow_unit = FlowUnit.M3_S
        
        # Facteurs de conversion DEPUIS les unités SI (Pa, m³/s) VERS l'unité d'affichage
        self.pressure_conversions = {
            PressureUnit.BAR: 1e-5,        # Pa -> bar
            PressureUnit.KPA: 1e-3,        # Pa -> kPa
            PressureUnit.PA: 1.0,          # Pa -> Pa
            PressureUnit.MCE: 1.0 / (1000 * 9.81),  # Pa -> mCE
        }
        
        self.flow_conversions = {
            FlowUnit.M3_S: 1.0,           # m³/s -> m³/s
            FlowUnit.M3_H: 3600.0,        # m³/s -> m³/h
            FlowUnit.L_S: 1000.0,         # m³/s -> L/s
            FlowUnit.L_MIN: 60000.0,      # m³/s -> L/min
            FlowUnit.L_H: 3600000.0,      # m³/s -> L/h
        }
        
        # Facteurs de conversion DEPUIS l'unité d'affichage VERS les unités SI
        self.pressure_input_conversions = {
            PressureUnit.BAR: 1e5,         # bar -> Pa
            PressureUnit.KPA: 1e3,         # kPa -> Pa
            PressureUnit.PA: 1.0,          # Pa -> Pa
            PressureUnit.MCE: 1000 * 9.81, # mCE -> Pa
        }
        
        self.flow_input_conversions = {
            FlowUnit.M3_S: 1.0,            # m³/s -> m³/s
            FlowUnit.M3_H: 1.0/3600.0,     # m³/h -> m³/s
            FlowUnit.L_S: 1.0/1000.0,      # L/s -> m³/s
            FlowUnit.L_MIN: 1.0/60000.0,   # L/min -> m³/s
            FlowUnit.L_H: 1.0/3600000.0,   # L/h -> m³/s
        }
        
        # Charger les préférences utilisateur si elles existent
        self.load_settings()
        
        UnitManager._initialized = True
    
    @classmethod
    def get_instance(cls):
        """Méthode alternative pour obtenir l'instance (plus explicite)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_pressure_unit(self, unit: PressureUnit):
        """Définir l'unité de pression pour l'affichage"""
        self.pressure_unit = unit
        self.save_settings()  # Sauvegarder automatiquement les préférences
    
    def set_flow_unit(self, unit: FlowUnit):
        """Définir l'unité de débit pour l'affichage"""
        self.flow_unit = unit
        self.save_settings()  # Sauvegarder automatiquement les préférences
    
    # === MÉTHODES POUR L'AFFICHAGE (SI -> Unité choisie) ===
    
    def display_pressure(self, pressure_pa: Optional[float]) -> Optional[float]:
        """Convertir une pression depuis Pa vers l'unité d'affichage"""
        if pressure_pa is None:
            return None
        return pressure_pa * self.pressure_conversions[self.pressure_unit]
    
    def display_flow(self, flow_m3s: Optional[float]) -> Optional[float]:
        """Convertir un débit depuis m³/s vers l'unité d'affichage"""
        if flow_m3s is None:
            return None
        return float(flow_m3s) * self.flow_conversions[self.flow_unit]
    
    def format_pressure(self, pressure_pa: Optional[float], precision: int = 2) -> str:
        """Formater une pression (stockée en Pa) pour l'affichage"""
        if pressure_pa is None:
            return "N/A"
        converted = self.display_pressure(pressure_pa)
        return f"{converted:.{precision}f} {self.pressure_unit.value}"
    
    def format_flow(self, flow_m3s: Optional[float], precision: int = 2) -> str:
        """Formater un débit (stocké en m³/s) pour l'affichage"""
        if flow_m3s is None:
            return "N/A"
        converted = self.display_flow(flow_m3s)
        return f"{converted:.{precision}f} {self.flow_unit.value}"
    
    # === MÉTHODES POUR LA SAISIE (Unité choisie -> SI) ===
    
    def input_pressure_to_pa(self, pressure_value: float, unit: PressureUnit = None) -> float:
        """Convertir une pression saisie vers Pa (pour stockage interne)"""
        if unit is None:
            unit = self.pressure_unit
        return pressure_value * self.pressure_input_conversions[unit]
    
    def input_flow_to_m3s(self, flow_value: float, unit: FlowUnit = None) -> float:
        """Convertir un débit saisi vers m³/s (pour stockage interne)"""
        if unit is None:
            unit = self.flow_unit
        return flow_value * self.flow_input_conversions[unit]
    
    # === MÉTHODES UTILITAIRES ===
    
    def get_pressure_unit_symbol(self) -> str:
        """Obtenir le symbole de l'unité de pression actuelle"""
        return self.pressure_unit.value
    
    def get_flow_unit_symbol(self) -> str:
        """Obtenir le symbole de l'unité de débit actuelle"""
        return self.flow_unit.value
    
    def get_available_pressure_units(self) -> Dict[str, str]:
        """Retourner les unités de pression disponibles"""
        return {unit.name: unit.value for unit in PressureUnit}
    
    def get_available_flow_units(self) -> Dict[str, str]:
        """Retourner les unités de débit disponibles"""
        return {unit.name: unit.value for unit in FlowUnit}
    
    # === PERSISTANCE DES PRÉFÉRENCES ===
    
    def save_settings(self, filepath: str = "unit_settings.json"):
        """Sauvegarder les paramètres d'unités"""
        settings = {
            "pressure_unit": self.pressure_unit.value,
            "flow_unit": self.flow_unit.value
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des unités: {e}")
    
    def load_settings(self, filepath: str = "unit_settings.json"):
        """Charger les paramètres d'unités"""
        try:
            with open(filepath, 'r') as f:
                settings = json.load(f)
            
            # Convertir les strings en enums
            for unit in PressureUnit:
                if unit.value == settings.get("pressure_unit"):
                    self.pressure_unit = unit
                    break
            
            for unit in FlowUnit:
                if unit.value == settings.get("flow_unit"):
                    self.flow_unit = unit
                    break
                    
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Utiliser les valeurs par défaut si problème de chargement
            pass
    
    def set_units_from_names(self, pressure_unit_name: str, flow_unit_name: str) -> bool:
        """Définir les unités depuis leurs noms (pour interface utilisateur)"""
        try:
            pressure_unit = PressureUnit[pressure_unit_name.upper()]
            flow_unit = FlowUnit[flow_unit_name.upper()]
            
            self.set_pressure_unit(pressure_unit)
            self.set_flow_unit(flow_unit)
            
            return True
        except KeyError:
            return False

# Fonction de commodité pour obtenir l'instance unique
def get_unit_manager() -> UnitManager:
    """Fonction de commodité pour obtenir l'instance unique du UnitManager"""
    return UnitManager.get_instance()