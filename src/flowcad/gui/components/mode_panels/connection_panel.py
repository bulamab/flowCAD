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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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

        
        # Style des boutons
        button_style = """
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

        self.create_mode_btn.setStyleSheet(button_style + "background-color: #4CAF50; color: white;")

        # Connecter les boutons
        self.create_mode_btn.clicked.connect(lambda: self.set_mode("create"))

        layout.addWidget(self.create_mode_btn)

        layout.addStretch()  # pousse tout vers le haut