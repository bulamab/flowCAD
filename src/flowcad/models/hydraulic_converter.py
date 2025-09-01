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
    
    #convertir la pression de mCE en bar
    @staticmethod
    def P_mCE_to_bar(pressure_mCE: float) -> float:
        """
        Convertir la pression (en mCE) en pression (en bars).
        Utilise la formule: P = ρ * g * H
        """
        g = 9.81  # Accélération due à la gravité en m/s²
        rho = 1000  # Densité du fluide de référence en kg/m³ 
        pressure_pa = rho * g * pressure_mCE
        pressure_bar = pressure_pa / 1e5  # Convertir Pascals en bars
        return pressure_bar
    
    #convertir la pression de mCE en Pa
    @staticmethod
    def P_mCE_to_Pa(pressure_mCE: float) -> float:
        """
        Convertir la pression (en mCE) en pression (en Pascals).
        Utilise la formule: P = ρ * g * H
        """
        g = 9.81  # Accélération due à la gravité en m/s²
        rho = 1000  # Densité du fluide de référence en kg/m³
        pressure_pa = rho * g * pressure_mCE
        return pressure_pa
    
    #convertir la pression de mCE en kPa
    @staticmethod
    def P_mCE_to_kPa(pressure_mCE: float) -> float:
        """
        Convertir la pression (en mCE) en pression (en kPa).
        Utilise la formule: P = ρ * g * H
        """
        return HydraulicConverter.P_mCE_to_Pa(pressure_mCE) / 1000
    
    #methode qui calcule un zeta à partir des conditions nominales (débit et pertes de charges)
    @staticmethod
    def zeta_from_nominal_conditions(flow_rate_m3s: float, head_loss_kPa: float, diameter: float, fluid: Fluid=Fluid()) -> float:
        """
        Calcule le coefficient de perte de charge (zeta) à partir des conditions nominales.
        """
        velocity = (4 * abs(flow_rate_m3s)) / (3.14159 * diameter**2)  # V = Q / A
        rho = fluid.density  # Densité du fluide en kg/m³
        if velocity == 0:
            return 0.0
        return 2*head_loss_kPa*1000 / (velocity ** 2*rho)  # zeta = 2*ΔP / (ρ * V²)
    
    #methode qui calcule un zeta à partir d'un kv
    @staticmethod
    def zeta_from_kv(kv: float, diameter: float, fluid: Fluid=Fluid()) -> float:
        """
        Calcule le coefficient de perte de charge (zeta) à partir du kv.
        """
        return HydraulicConverter.zeta_from_nominal_conditions(flow_rate_m3s=kv/3600, head_loss_kPa=100, diameter=diameter, fluid=fluid)
    
    #méthode qui convertit les débits de m3/h en m3/s
    def m3h_to_m3s(flow_rate_m3h: float) -> float:
        return flow_rate_m3h / 3600

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