"""
Panneau des connexions
"""
from tokenize import group
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QListWidget, QListWidgetItem, QHBoxLayout,
                            QGroupBox, QComboBox, QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Dict

class ConnectionPanel(QWidget):
    """Panneau pour gérer les connexions entre équipements"""
    
    # Signaux émis par le panneau
    connection_mode_changed = pyqtSignal(str)
    ports_visibility_changed = pyqtSignal(bool)

    pipe_properties_response = pyqtSignal(dict)

    DEFAULT_DIAMETER = 0.1  # m
    DEFAULT_LENGTH = 1.0    # m
    DEFAULT_ROUGHNESS = 0.1  # mm
    
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
        layout.setSpacing(20)
        
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

        # --- Groupe de propriétés ---
        group = QGroupBox("Propriétés du tuyau")

        #les propiétés: 
        self.diametre_edit = QLineEdit()
        self.diametre_edit.setText(str(self.DEFAULT_DIAMETER))
        self.longueur_edit = QLineEdit()
        self.longueur_edit.setText(str(self.DEFAULT_LENGTH))
        self.roughness_edit = QLineEdit()
        self.roughness_edit.setText(str(self.DEFAULT_ROUGHNESS))

        # Forcer fond blanc
        for edit in (self.diametre_edit, self.longueur_edit, self.roughness_edit):
            edit.setStyleSheet("background-color: white;")
        # Layout interne du groupe
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Diamètre (m) :"), self.diametre_edit)
        form_layout.addRow(QLabel("Longueur (m) :"), self.longueur_edit)
        form_layout.addRow(QLabel("Rugosité (mm) :"), self.roughness_edit)

        group.setLayout(form_layout)
        layout.addWidget(group)

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
    #obtenir les propriétés du tuyau
    def get_pipe_properties(self) -> Dict[str, float]:
        """Retourne les propriétés du tuyau"""
        return {
            "diameter_m": float(self.diametre_edit.text()),
            "length_m": float(self.longueur_edit.text()),
            "roughness_mm": float(self.roughness_edit.text())
        }
    
    def send_pipe_properties(self):
        """Envoie les propriétés actuelles du tuyau"""
        properties = self.get_pipe_properties()
        self.pipe_properties_response.emit(properties)
        print(f"Propriétés envoyées : {properties}")
