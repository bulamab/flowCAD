"""
Panneau des connexions
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QListWidget, QListWidgetItem, QHBoxLayout,
                            QGroupBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ConnectionPanel(QWidget):
    """Panneau pour gérer les connexions entre équipements"""
    
    # Signaux émis par le panneau
    connection_mode_changed = pyqtSignal(str)
    ports_visibility_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Style des boutons par défaut
        self.button_style = """
            QPushButton {
                color: black;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #4CAF50;
                color: white;
            }
        """

        self.button_active_style = """
            QPushButton {
                color: white;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #4CAF50;
                text-align: center;
            }
        """
        self.current_mode = "select"
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du panneau connexions"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # === TITRE ===
        title = QLabel("Gestion des Connexions")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; padding: 5px; border-bottom: 2px solid #ddd;")
        title.setMaximumHeight(30)
        layout.addWidget(title)
    
        
        # Boutons de mode
        self.create_mode_btn = QPushButton("Création de tuyau")

        self.create_mode_btn.setStyleSheet(self.button_style)

        # Connecter les boutons
        self.create_mode_btn.clicked.connect(lambda: self.set_mode("create"))

        layout.addWidget(self.create_mode_btn)

        # Checkbox pour contrôler l'affichage des ports
        from PyQt5.QtWidgets import QCheckBox
        
        self.show_connected_ports_cb = QCheckBox("Afficher ports connectés")
        self.show_connected_ports_cb.setChecked(False)  # Cachés par défaut
        self.show_connected_ports_cb.toggled.connect(self.on_show_ports_toggled)
        layout.addWidget(self.show_connected_ports_cb)

        layout.addStretch()  # pousse tout vers le haut

    def on_show_ports_toggled(self, checked):
        """Callback de la checkbox d'affichage des ports"""
        print(f"👻 Affichage ports connectés: {'ON' if checked else 'OFF'}")
        # Émettre un signal
        self.ports_visibility_changed.emit(checked)

    #fonction appelée en cas d'appui de l'utilisateur sur le bouton create
    def set_mode(self, mode):
        """Change le mode de connexion"""
        print(f"🔧 Mode connexion changé vers: {mode}")
        
        current_mode = self.get_current_mode()
        #si on est déjà dans ce mode, revenir au mode select
        if mode == current_mode:
            self.reset_mode()
            self.connection_mode_changed.emit(mode)
            return

        self.current_mode = mode  # ✅ Sauvegarder l'état actuel    
        
        if mode == "create":
            # Activer le mode création de tuyau
            self.create_mode_btn.setStyleSheet(self.button_active_style)
        else:
            # Style bouton normal
            self.create_mode_btn.setStyleSheet(self.button_style)

        #emet signal pour avertir du changement de mode
        self.connection_mode_changed.emit(mode)
    
    # ✅ NOUVELLE MÉTHODE : Réinitialiser le mode
    def reset_mode(self):
        """Remet le panneau en mode normal (select)"""
        print("🔄 Réinitialisation du mode connexion")
        self.set_mode("select")
    
    # ✅ NOUVELLE MÉTHODE : Obtenir l'état actuel
    def get_current_mode(self):
        """Retourne le mode actuel"""
        return self.current_mode
    
    # ✅ NOUVELLE MÉTHODE : Vérifier si en mode création
    def is_in_create_mode(self):
        """Vérifie si le panneau est en mode création"""
        return self.current_mode == "create"
