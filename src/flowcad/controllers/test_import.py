# test_imports.py
try:
    print("Test des imports...")
    
    print("1. WNTR...")
    import wntr
    print("   ✅ WNTR OK")
    
    print("2. Models hydrauliques...")
    from src.flowcad.models.hydraulique.components import HydraulicComponent
    print("   ✅ Composants hydrauliques OK")
    
    print("3. Équipements...")
    from src.flowcad.models.equipment.base_equipment import BaseEquipment
    print("   ✅ Équipements de base OK")
    
    print("4. Réseau d'équipements...")
    from src.flowcad.models.equipment.network_equipment import NetworkEquipment
    print("   ✅ Réseau d'équipements OK")
    
    print("5. Contrôleur de simulation...")
    from src.flowcad.controllers.simulation_controller import SimulationController
    print("   ✅ Contrôleur de simulation OK")
    
    print("\n🎉 Tous les imports fonctionnent !")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print(f"Vérifiez l'installation des dépendances et la structure des fichiers")