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
from .components.right_panel import RightPanel
from .components.drawing_canvas import DrawingCanvas
from ..config.equipment.equipment_loader import EquipmentLoader
from .components.mode_panels.connection_panel import ConnectionPanel

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
        #self.drawing_canvas.pipe_properties_requested.connect(self.on_pipe_properties_requested)
        

        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)  # Pas de marges
        main_layout.setSpacing(0)  # Pas d'espacement
        
        # Ajouter la barre d'outils ribbon en haut
        self.ribbon_toolbar = RibbonToolbar(self)
        self.ribbon_toolbar.rotate_equipment.connect(self.on_rotate_equipment)
        self.ribbon_toolbar.mirror_equipment.connect(self.on_mirror_equipment)
        self.ribbon_toolbar.align_equipment.connect(self.on_align_equipment)
        self.ribbon_toolbar.distribute_equipment.connect(self.on_distribute_equipment)
        main_layout.addWidget(self.ribbon_toolbar)
        
        # Layout horizontal pour les panneaux du bas
        panels_layout = QHBoxLayout()
        panels_layout.setContentsMargins(1, 1, 1, 1)
        panels_layout.setSpacing(0)
        
        # Panneau équipement à gauche
        self.Left_panel = LeftPanel(self)
        panels_layout.addWidget(self.Left_panel)
        self.Left_panel.get_connection_panel().connection_mode_changed.connect(self.on_connection_mode_changed)
        self.Left_panel.get_connection_panel().ports_visibility_changed.connect(self.on_ports_visibility_changed)
        # Quand le canvas demande les propriétés -> le panneau les envoie
        self.drawing_canvas.pipe_properties_requested.connect(
            self.Left_panel.get_connection_panel().send_pipe_properties
        )
        # Quand le panneau envoie les propriétés -> le canvas les reçoit
        self.Left_panel.get_connection_panel().pipe_properties_response.connect(
            self.drawing_canvas.pipe_properties_received)

        # Connecter le signal de fin de création de polyligne
        self.drawing_canvas.polyline_creation_finished.connect(self.on_polyline_creation_finished)
        
        # Zone de dessin au centre
        #self.drawing_canvas = DrawingCanvas(self)
        panels_layout.addWidget(self.drawing_canvas)

        #panneau des proporiétés à droite
        self.Right_panel = RightPanel(self)
        panels_layout.addWidget(self.Right_panel)
        # Connecter le signal d'équipement sélectionné pour charger les propriétés
        self.drawing_canvas.equipment_properties_requested.connect(self.Right_panel.display_properties)
        self.Right_panel.equipment_update_requested.connect(self.update_equipment_properties)
        self.Right_panel.pipe_update_requested.connect(self.update_pipe_properties)

        

        # Ajouter le layout des panneaux au layout principal
        main_layout.addLayout(panels_layout)

        #setup de la barre de status
        self.statusBar().showMessage("Prêt")

    #------------------ fonctions liés aux changements des équipements ---------------------------

    def on_equipment_dropped(self, equipment_id, equipment_def, position):
        print(f"Nouvel équipement: {equipment_id}")
        #self.update_status_message(f"Équipement ajouté: {equipment_def.get('display_name')}")
    
    def on_equipment_selected(self, equipment_id):
        print(f"Équipement sélectionné: {equipment_id}")
        # Mettre à jour le panneau des propriétés
    
    def on_port_selected(self, equipment_id, port_id):
        print(f"Port sélectionné: {port_id} de {equipment_id}")
        # Préparer le mode connexion

    def on_rotate_equipment(self, angle):
        print(f"Rotation de l'équipement sélectionné de {angle}°")
        self.drawing_canvas.rotate_selected_equipment(angle)

    def on_mirror_equipment(self, direction):
        print(f"Miroir de l'équipement sélectionné: {direction}")
        self.drawing_canvas.mirror_selected_equipment(direction)

    def on_align_equipment(self, direction):
        print(f"Alignement de l'équipement sélectionné: {direction}")
        self.drawing_canvas.align_selected_equipment(direction)

    def on_distribute_equipment(self, direction):
        print(f"Distribution de l'équipement sélectionné: {direction}")
        self.drawing_canvas.distribute_selected_equipment(direction)

    #------------- fonction liée au changement de mode Equipement/Connexion

    def on_panel_mode_changed(self, mode):
        """Callback quand le mode du panneau gauche change"""
        print(f"🔄 Mode du panneau changé vers: {mode}")
        
        if mode == "equipment":
            self.current_work_mode = WorkModes.EQUIPMENT
            self.statusBar().showMessage("Mode: Équipements")
        elif mode == "connection":
            self.current_work_mode = WorkModes.CONNECTION
            self.statusBar().showMessage("Mode: Connexions")
        
        # Émettre le signal de changement de mode
        self.work_mode_changed.emit(self.current_work_mode)

        
        self.statusBar().showMessage(f"Mode connexion: {mode_text}")

    #------------ fonctions liées au mode connection ------------------------------

    def on_connection_mode_changed(self, connection_mode):
        """Callback quand le mode de connexion change"""
        print(f"🔌 Mode de connexion changé vers: {connection_mode}")
        
        if connection_mode == "create":
            # Activer le mode création de polyligne sur le canvas
            self.drawing_canvas.set_interaction_mode("create_polyline")
            self.statusBar().showMessage("Mode: Création de tuyau - Cliquez sur un port pour commencer")
        else:
            # Retour au mode normal
            self.drawing_canvas.set_interaction_mode("select")
            self.statusBar().showMessage("Mode: Sélection")

    def on_polyline_creation_finished(self):
        """Callback quand une polyligne est terminée (créée ou annulée)"""
        print("🏁 Création de polyligne terminée - reset du panneau connexion")
        
        # Remettre le panneau connexion en mode normal
        connection_panel = self.Left_panel.get_connection_panel()
        if connection_panel.is_in_create_mode():
            connection_panel.reset_mode()
            print("✅ Bouton 'Création de tuyau' remis à l'état normal")
        
        # Mettre à jour la barre de statut
        self.statusBar().showMessage("Mode: Sélection")

    def on_ports_visibility_changed(self, visible):
        """Callback quand l'utilisateur change la visibilité des ports"""
        print(f"🎛️ Demande de changement visibilité ports: {visible}")
        self.drawing_canvas.set_connected_ports_visibility(visible)
        
        status_msg = "affichés" if visible else "cachés"
        self.statusBar().showMessage(f"Ports connectés {status_msg}", 2000)

    #fonctions liées au changement des propriétés des éleéments via le panel de droite
    def update_equipment_properties(self, equipment_id, updated_properties):
        """Met à jour les propriétés d'un équipement donné"""
        print(f"🔄 Mise à jour des propriétés de {equipment_id}: {updated_properties}")
        self.drawing_canvas.update_equipment_properties(equipment_id=equipment_id, new_properties=updated_properties)

    #fonction liées au changement des proporiétés des pipes via le panel de droite
    def update_pipe_properties(self, pipe_id, updated_properties):
        """Met à jour les propriétés d'un tuyau donné"""
        print(f"🔄 Mise à jour des propriétés du tuyau {pipe_id}: {updated_properties}")
        self.drawing_canvas.update_pipe_properties(pipe_id=pipe_id, new_properties=updated_properties)

    '''def on_pipe_properties_requested(self):
        """Callback pour fournir les propriétés du tuyau au canvas"""
        connection_panel = self.Left_panel.get_connection_panel()
        properties = connection_panel.get_pipe_properties()
        self.drawing_canvas.cached_pipe_properties = properties'''

def main():
    """Point d'entrée de l'application GUI"""
    app = QApplication(sys.argv)
    
    window = FlowCADMainWindow()
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())