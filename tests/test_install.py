"""
Script de vérification de l'installation FlowCAD
"""

def check_installation():
    """Vérifie tous les composants nécessaires"""
    
    print("🔍 Vérification de l'installation FlowCAD...")
    print("=" * 50)
    
    # Python version
    import sys
    print(f"✅ Python: {sys.version.split()[0]} ({sys.executable})")
    
    # Packages essentiels
    packages = [
        ('numpy', 'Calculs numériques'),
        ('pandas', 'Manipulation de données'), 
        ('wntr', 'Simulation hydraulique'),
        ('pytest', 'Framework de tests')
    ]
    
    missing_packages = []
    
    for package, description in packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'Version inconnue')
            print(f"✅ {package}: {version} - {description}")
        except ImportError:
            print(f"❌ {package}: NON INSTALLÉ - {description}")
            missing_packages.append(package)
    
    print("=" * 50)
    
    if missing_packages:
        print(f"⚠️  Packages manquants: {', '.join(missing_packages)}")
        print("Commande pour installer:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("🎉 Tous les packages sont installés !")
        return True

def test_wntr_basic():
    """Test basique de WNTR"""
    try:
        import wntr
        print(f"\n🧪 Test WNTR...")
        
        # Créer un réseau simple
        wn = wntr.network.WaterNetworkModel()
        wn.add_junction('J1', base_demand=0.0, elevation=10.0)
        wn.add_reservoir('R1', base_head=50.0)
        wn.add_pipe('P1', 'R1', 'J1', length=100, diameter=0.3)
        
        print(f"✅ Réseau créé: {len(list(wn.junction_name_list))} jonctions, {len(list(wn.pipe_name_list))} tuyaux")
        
        # Test simulation simple
        sim = wntr.sim.EpanetSimulator(wn)
        results = sim.run_sim()
        
        pressure = results.node['pressure'].loc[0, 'J1']
        print(f"✅ Simulation réussie: Pression J1 = {pressure:.2f} m")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur WNTR: {e}")
        return False

if __name__ == "__main__":
    install_ok = check_installation()
    
    if install_ok:
        wntr_ok = test_wntr_basic()
        if wntr_ok:
            print("\n🚀 Installation FlowCAD complète et fonctionnelle !")
        else:
            print("\n⚠️ WNTR installé mais problème de fonctionnement")
    else:
        print("\n❌ Installation incomplète")