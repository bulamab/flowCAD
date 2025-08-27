"""
Tests de base pour vérifier l'environnement
"""

def test_python_version():
    """Vérifie la version Python"""
    import sys
    print(f"Python version: {sys.version}")
    assert sys.version_info >= (3, 8)

def test_wntr_import():
    """Teste l'import de wntr"""
    import wntr
    print(f"✅ WNTR version: {wntr.__version__}")
    assert wntr is not None

def test_basic_math():
    """Test basique pour vérifier pytest"""
    assert 2 + 2 == 4
    print("✅ Math works!")

if __name__ == "__main__":
    test_python_version()
    test_wntr_import() 
    test_basic_math()
    print("🎉 Tous les tests de base passent !")