"""
Panneau equipement/connections selon choix
"""
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt

from .mode_panels.equipment_panel import EquipmentPanel

class LeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)  # Largeur fixe pour le panneau
        self.setStyleSheet("background-color: #e8e8e8; border-right: 1px solid #ccc;")
        
        # Pour l'instant, juste un label
        self.setup_ui()
    
    def setup_ui(self):
        """Configure le panneau équipement (vide pour l'instant)"""
        from PyQt5.QtWidgets import QVBoxLayout
        
        layout = QVBoxLayout(self)
        
        # Placeholder
        label = QLabel("🔧 Panneau gauche\n(à implémenter)")
        label.setAlignment(Qt.AlignCenter)
        label.setMaximumHeight(100)
        layout.addWidget(label)

        #Panel pour les équipements
        self.equipment_panel = EquipmentPanel(self)
        layout.addWidget(self.equipment_panel)