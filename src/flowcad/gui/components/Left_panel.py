"""
Panneau equipement/connections selon choix
"""
from PyQt5.QtWidgets import QWidget, QLabel, QTabWidget
from PyQt5.QtCore import Qt

from .mode_panels.equipment_panel import EquipmentPanel
from .mode_panels.connection_panel import ConnectionPanel

class LeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)  # Largeur fixe pour le panneau
        self.setStyleSheet("background-color: #e8e8e8; border-right: 1px solid #ccc;")
        
        # Pour l'instant, juste un label
        self.setup_ui()
    
    def setup_ui(self):
        """Configure le panneau équipement (vide pour l'instant)"""
        from PyQt5.QtWidgets import QVBoxLayout
        
        from PyQt5.QtWidgets import QVBoxLayout
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Créer le widget à onglets
        self.tab_widget = QTabWidget(self)
        
        # Style des onglets
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: white;
            }
            QTabWidget::tab-bar {
                left: 5px; /* décalage des onglets */
            }
            QTabBar::tab {
                min-width: 80px;  /* Largeur minimale de chaque onglet */
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-bottom-color: #ccc;
                padding: 8px 12px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
            QTabBar::tab:!selected {
                margin-top: 2px; /* décaler un peu les onglets non sélectionnés */
            }
        """)
        
        # Créer les panneaux
        self.equipment_panel = EquipmentPanel(self)
        self.connection_panel = ConnectionPanel(self)
        
        # Ajouter les onglets
        self.tab_widget.addTab(self.equipment_panel, "Équipements")
        self.tab_widget.addTab(self.connection_panel, "Connexions")
        
        # Connecter le signal de changement d'onglet
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Ajouter le widget d'onglets au layout
        layout.addWidget(self.tab_widget)
    
    def on_tab_changed(self, index):
        """Callback quand l'onglet change"""
        tab_names = ["Équipements", "Connexions"]
        if index < len(tab_names):
            print(f"🔄 Changement d'onglet vers: {tab_names[index]}")
            
            # Ici vous pouvez émettre un signal vers la fenêtre principale
            # pour changer le mode de travail si nécessaire
            if hasattr(self.parent(), 'on_panel_mode_changed'):
                mode = "equipment" if index == 0 else "connection"
                self.parent().on_panel_mode_changed(mode)
    
    def set_active_tab(self, tab_name):
        """Change l'onglet actif par programme"""
        tab_indices = {"equipment": 0, "connection": 1}
        if tab_name in tab_indices:
            self.tab_widget.setCurrentIndex(tab_indices[tab_name])
    
    def get_current_panel(self):
        """Retourne le panneau actuellement actif"""
        return self.tab_widget.currentWidget()
    
    def get_equipment_panel(self):
        """Retourne le panneau équipements"""
        return self.equipment_panel
    
    def get_connection_panel(self):
        """Retourne le panneau connexions"""
        return self.connection_panel