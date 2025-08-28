#Classe qui définit les propriétés de base d'un fluide, nécessaires pour les calculs hydrauliques


class Fluid:
    def __init__(self, name: str = "Water", viscosity: float = 1.004e-6, density: float = 1000.0):
        self.name = name  # Nom du fluide
        self.viscosity = viscosity  # Viscosité cinématique en m²/s (ex: eau à 20°C)
        self.density = density  # Gravité spécifique (ex: eau = 1.0)
    
    
    #fonction qui retourne la viscosité reltaive (dimensionless)
    def relative_viscosity(self, reference_viscosity: float = 1.004e-6) -> float:
        return self.viscosity / reference_viscosity
    
    #fonction qui retourne la gravité spécifique relative (dimensionless)
    def relative_density(self, reference_density: float = 1000.0) -> float:
        return self.density / reference_density
    
    def __str__(self) -> str:
        return f"Fluid(name='{self.name}', viscosity={self.viscosity} m²/s, density={self.density} kg/m³)"
    
    def __repr__(self) -> str:
        return f"Fluid(name='{self.name}', viscosity={self.viscosity}, density={self.density} kg/m³)"

#Test simple de la classe Fluid
if __name__ == "__main__":
    water = Fluid()
    oil = Fluid(name="Oil", viscosity=0.1e-6, density=800.0)
    print(water)
    print(oil)