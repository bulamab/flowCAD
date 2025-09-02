"""
Fenêtre principale de FlowCAD
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

from enum import Enum

from .components.ribbon_toolbar import RibbonToolbar
from .components.Left_panel import LeftPanel
from .components.drawing_canvas import DrawingCanvas
from ..config.equipment.equipment_loader import EquipmentLoader

class WorkModes(Enum):
    EQUIPMENT = "Équipement"
    CONNECTION = "Connexion"
    SIMULATION = "Simulation"

class FlowCADMainWindow(QMainWindow):

    #signal émis en cas de changement de mode de travail
    work_mode_changed = pyqtSignal(WorkModes)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowCAD - Conception de Réseaux Hydrauliques")
        self.setGeometry(100, 100, 1200, 800)
        self.current_work_mode = WorkModes.EQUIPMENT #le mode de travail au lancement de l'application
        
        #Créer le loader de configuration
        self.equipment_loader = EquipmentLoader()

        # Créer le canvas
        self.drawing_canvas = DrawingCanvas()
        
        # Connecter votre equipment_loader
        self.drawing_canvas.set_equipment_loader(self.equipment_loader)

        # Connecter les signaux
        self.drawing_canvas.equipment_dropped.connect(self.on_equipment_dropped)
        self.drawing_canvas.equipment_selected.connect(self.on_equipment_selected)
        self.drawing_canvas.port_selected.connect(self.on_port_selected)

        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges
        main_layout.setSpacing(0)  # Pas d'espacement
        
        # Ajouter la barre d'outils ribbon en haut
        self.ribbon_toolbar = RibbonToolbar(self)

        main_layout.addWidget(self.ribbon_toolbar)
        
        # Layout horizontal pour les panneaux du bas
        panels_layout = QHBoxLayout()
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(0)
        
        # Panneau équipement à gauche
        self.Left_panel = LeftPanel(self)
        panels_layout.addWidget(self.Left_panel)
        
        # Zone de dessin au centre
        #self.drawing_canvas = DrawingCanvas(self)
        panels_layout.addWidget(self.drawing_canvas)

        # Ajouter le layout des panneaux au layout principal
        main_layout.addLayout(panels_layout)

        #setup de la barre de status
        self.statusBar().showMessage("Prêt")

    def on_equipment_dropped(self, equipment_id, equipment_def, position):
        print(f"Nouvel équipement: {equipment_id}")
        #self.update_status_message(f"Équipement ajouté: {equipment_def.get('display_name')}")
    
    def on_equipment_selected(self, equipment_id):
        print(f"Équipement sélectionné: {equipment_id}")
        # Mettre à jour le panneau des propriétés
    
    def on_port_selected(self, equipment_id, port_id):
        print(f"Port sélectionné: {port_id} de {equipment_id}")
        # Préparer le mode connexion


def main():
    """Point d'entrée de l'application GUI"""
    app = QApplication(sys.argv)
    
    window = FlowCADMainWindow()
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())