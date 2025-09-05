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

        layout.addStretch()  # pousse tout vers le haut

    #fonction appelée en cas d'appui de l'utilisateur sur le bouton create
    def set_mode(self, mode):
        """Change le mode de connexion"""
        print(f"🔧 Mode connexion changé vers: {mode}")
        
        ##MAB: attention, à adapter pour quitter le mode creation...
        
        if mode == "create":
            # Activer le mode création de tuyau
            self.create_mode_btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #4CAF50;
                    text-align: center;
                }
            """)
        else:
            # Style bouton normal
            self.create_mode_btn.setStyleSheet("""
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
            """)

        #emet signal pour avertir du changement de mode
        self.connection_mode_changed.emit(mode)
