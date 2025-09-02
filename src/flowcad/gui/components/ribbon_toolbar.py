"""
Barre d'outils style ribbon pour FlowCAD
"""
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt


class RibbonToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)  # Hauteur fixe pour le ribbon
        self.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc;")
        
        # Pour l'instant, juste un label
        self.setup_ui()
    
    def setup_ui(self):
        """Configure le ribbon toolbar (vide pour l'instant)"""
        from PyQt5.QtWidgets import QHBoxLayout
        
        layout = QHBoxLayout(self)
        
        # Placeholder
        label = QLabel("🛠️ Ribbon Toolbar (à implémenter)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
