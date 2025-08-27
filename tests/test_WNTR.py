"""
Test WNTR minimaliste : 2 réservoirs à hauteurs différentes avec 1 tuyau
Calcule le débit entre les réservoirs
"""

import wntr


def test_with_junction():
    """
    Variant avec une jonction intermédiaire pour plus de réalisme
    R1 ---> J1 ---> R2
    """
    print("\n=== Test avec jonction intermédiaire ===")
    
    wn = wntr.network.WaterNetworkModel()
    
    # Réservoirs
    wn.add_reservoir('R1', base_head=50.0)
    wn.add_reservoir('R2', base_head=10.0)
    
    # Jonction intermédiaire (avec petite demande pour forcer l'écoulement)
    wn.add_junction('J1', base_demand=0, elevation=0.0)  # 1 L/s de demande
    
    # Tuyaux
    wn.add_pipe('P1', 'R1', 'J1', length=500.0, diameter=0.25, roughness=0.0002)
    wn.add_pipe('P2', 'J1', 'R2', length=500.0, diameter=0.25, roughness=0.0002)
    wn.add_pipe('P3', 'R1', 'R2', length=1000.0, diameter=0.25, roughness=0.0002)
    
    # Simulation
    wn.options.time.duration = 3600  # 1 heure
    wn.options.time.hydraulic_timestep = 3600  # Pas de 1 heure
    wn.options.time.report_timestep = 3600
    wn.options.hydraulic.headloss = 'D-W'

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim(convergence_error=True)
    
    # Résultats
    print("Pressions:")
    print(f"  R1: {results.node['pressure'].loc[0, 'R1']:.2f} m")
    print(f"  J1: {results.node['pressure'].loc[0, 'J1']:.2f} m") 
    print(f"  R2: {results.node['pressure'].loc[0, 'R2']:.2f} m")


    print("Heads:")
    print(f"  R1: {results.node['head'].loc[0, 'R1']:.2f} m")
    print(f"  J1: {results.node['head'].loc[0, 'J1']:.2f} m") 
    print(f"  R2: {results.node['head'].loc[0, 'R2']:.2f} m")
    
    print("Débits:")
    print(f"  P1: {results.link['flowrate'].loc[0, 'P1']*1000:.2f} L/s")
    print(f"  P2: {results.link['flowrate'].loc[0, 'P2']*1000:.2f} L/s")
    print(f"  P3: {results.link['flowrate'].loc[0, 'P3']*1000:.2f} L/s")    

    print("Pertes de charge:")
    print(f"  P1: {results.link['headloss'].loc[0, 'P1']:.2f} m")
    print(f"  P2: {results.link['headloss'].loc[0, 'P2']:.2f} m")
    print(f"  P3: {results.link['headloss'].loc[0, 'P3']:.2f} m")  

    link_keys = results.link.keys()

    print(link_keys)

    print("Coefficient de friction:")
    print(f"  P1: {results.link['friction_factor'].loc[0, 'P1']:.4f} -")
    print(f"  P2: {results.link['friction_factor'].loc[0, 'P2']:.4f} -")
    print(f"  P3: {results.link['friction_factor'].loc[0, 'P3']:.4f} -") 

    return results


#Test minimal, 2 réservoirs, une pompe, un tuyau
def test_with_pump():
    print("\n=== Test minimal avec pompe ===")
    
    wn = wntr.network.WaterNetworkModel()
    
    # Réservoirs
    wn.add_reservoir('R1', base_head=10.0)
    wn.add_reservoir('R2', base_head=50.0)

    #jonction intermédiaire 
    wn.add_junction('J1', base_demand=0, elevation=0.0)  # 
    
    # Tuyaux
    wn.add_pipe('P1', 'R1', 'J1', length=1000.0, diameter=0.25, roughness=0.0002)
    
    #courbe de pompe (Q, H)
    curve_points = [(20, 40)]  # Débit de 20 L/s à une hauteur de 40 m
    curbe_name = 'pump_curve'
    wn.add_curve(name=curbe_name, curve_type='HEAD', xy_tuples_list=curve_points)
    # Ajouter la pompe
    wn.add_pump('PU1', 'J1', 'R2', pump_type='HEAD', pump_parameter=curbe_name)  # Pompe avec courbe définie
    
    # Simulation
    wn.options.time.duration = 3600  # 1 heure
    wn.options.time.hydraulic_timestep = 3600  # Pas de 1 heure
    wn.options.time.report_timestep = 3600
    wn.options.hydraulic.headloss = 'D-W'

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim(convergence_error=True)
    
    # Résultats
    print("Pressions:")
    print(f"  R1: {results.node['pressure'].loc[0, 'R1']:.2f} m")
    print(f"  R2: {results.node['pressure'].loc[0, 'R2']:.2f} m")

    print("Heads:")
    print(f"  R1: {results.node['head'].loc[0, 'R1']:.2f} m")
    print(f"  R2: {results.node['head'].loc[0, 'R2']:.2f} m")
    
    print("Débits:")
    print(f"  P1: {results.link['flowrate'].loc[0, 'P1']*1000:.2f} L/s")
    print(f"  PU1: {results.link['flowrate'].loc[0, 'PU1']*1000:.2f} L/s")

    print("Pertes de charge:")
    print(f"  P1: {results.link['headloss'].loc[0, 'P1']:.2f} m")


if __name__ == "__main__":
    
    # Test avec jonction
    #results2 = test_with_junction()

    # Test minimal avec pompe
    results1 = test_with_pump()
    
    print("\nTests terminés. Analysez les débits obtenus !")