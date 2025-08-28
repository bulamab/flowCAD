from .fluid import Fluid

class HydraulicConverter:
    """
    Classe pour convertir des propriétés de fluides entre différentes unités ou systèmes.
    """
    @staticmethod
    def pressure_to_head(pressure_bar: float, elevation: float, fluid: Fluid=Fluid()) -> float:
        """
        Convertir la pression (en bars) wr l'élévration (en mètres) en hauteur de colonne de fluide (en mètres).
        Utilise la formule: H = P / (ρ * g) + z
        """
        g = 9.81  # Accélération due à la gravité en m/s²
        rho = fluid.density  # Densité du fluide en kg/m³
        pressure_pa = pressure_bar * 1e5  # Convertir bars en Pascals
        head = (pressure_pa / (rho * g)) + elevation
        return head
    
    #convertir la hauteur de colonne de fluide (en mètres) en pression (en bars)
    @staticmethod
    def head_to_pressure(head: float, elevation: float, fluid: Fluid=Fluid()) -> float:
        """
        Convertir la hauteur de colonne de fluide (en mètres) wr l'élévation (en mètres) en pression (en bars).
        Utilise la formule: P = ρ * g * (H - z)
        """
        g = 9.81  # Accélération due à la gravité en m/s²
        rho = fluid.density  # Densité du fluide en kg/m³
        pressure_pa = rho * g * (head - elevation)
        pressure_bar = pressure_pa / 1e5  # Convertir Pascals en bars
        return pressure_bar
    
#Test simple de la classe HydraulicConverter
if __name__ == "__main__":
    water = Fluid() # Eau par défaut
    oil = Fluid(name="Oil", viscosity=0.1e-6, density=800.0) # Huile
    pressure = 2.0  # en bars
    elevation = 10.0  # en mètres
    head_water = HydraulicConverter.pressure_to_head(pressure, elevation, water)
    head_oil = HydraulicConverter.pressure_to_head(pressure, elevation, oil)
    print(f"Hauteur de colonne d'eau pour {pressure} bars à {elevation} m: {head_water:.2f} m")
    print(f"Hauteur de colonne d'huile pour {pressure} bars à {elevation} m: {head_oil:.2f} m")
    head = 30.0  # en mètres
    pressure_water = HydraulicConverter.head_to_pressure(head, elevation, water)   
    pressure_oil = HydraulicConverter.head_to_pressure(head, elevation, oil)
    print(f"Pression d'eau pour {head} m à {elevation} m: {pressure_water:.2f} bars")
    print(f"Pression d'huile pour {head} m à {elevation} m: {pressure_oil:.2f} bars")   