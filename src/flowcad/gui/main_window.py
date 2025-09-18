"""
Fenêtre principale de FlowCAD
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

from enum import Enum

from .components.ribbon_toolbar import RibbonToolbar
from .components.Left_panel import LeftPanel
from .components.right_panel import RightPanel
from .components.drawing_canvas import DrawingCanvas
from ..config.equipment.equipment_loader import EquipmentLoader
from .components.mode_panels.connection_panel import ConnectionPanel
from ..file_io.file_manager import FlowCADFileManager

from ..controllers.simulation_controller import SimulationController

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

        #Créer le gestionnaire de fichiers
        self.file_manager = FlowCADFileManager()
        
        #Créer le loader de configuration
        self.equipment_loader = EquipmentLoader()

        # Créer le canvas
        self.drawing_canvas = DrawingCanvas()

        # Connecter votre equipment_loader
        self.drawing_canvas.set_equipment_loader(self.equipment_loader)

        # Panneau équipement à gauche
        self.Left_panel = LeftPanel(self)

        #panneau des proporiétés à droite
        self.Right_panel = RightPanel(self)

        # Créer le contrôleur de simulation
        self.simulation_controller = SimulationController(self)

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
        # Connecter le bouton calculer
        self.ribbon_toolbar.calculate_network.connect(self.run_simulation)
        #connecter les signaux du menu fichier
        self.ribbon_toolbar.save_file.connect(self.save_project)
        self.ribbon_toolbar.open_file.connect(self.open_project)
        self.ribbon_toolbar.new_file.connect(self.new_project)



        main_layout.addWidget(self.ribbon_toolbar)
        
        # Layout horizontal pour les panneaux du bas
        panels_layout = QHBoxLayout()
        panels_layout.setContentsMargins(1, 1, 1, 1)
        panels_layout.setSpacing(0)
        
        # Panneau équipement à gauche
        #self.Left_panel = LeftPanel(self)
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
        #self.Right_panel = RightPanel(self)
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
        #print(f"Nouvel équipement: {equipment_id}")
        #self.update_status_message(f"Équipement ajouté: {equipment_def.get('display_name')}")

        # Marquer le projet comme modifié
        self.file_manager.set_modified(True)
        self.update_window_title()
    
    def on_equipment_selected(self, equipment_id):
        #print(f"Équipement sélectionné: {equipment_id}")
        # Mettre à jour le panneau des propriétés
        pass
    
    def on_port_selected(self, equipment_id, port_id):
        #print(f"Port sélectionné: {port_id} de {equipment_id}")
        # Préparer le mode connexion
        pass

    def on_rotate_equipment(self, angle):
        #print(f"Rotation de l'équipement sélectionné de {angle}°")
        self.drawing_canvas.rotate_selected_equipment(angle)

    def on_mirror_equipment(self, direction):
        #print(f"Miroir de l'équipement sélectionné: {direction}")
        self.drawing_canvas.mirror_selected_equipment(direction)

    def on_align_equipment(self, direction):
        #print(f"Alignement de l'équipement sélectionné: {direction}")
        self.drawing_canvas.align_selected_equipment(direction)

    def on_distribute_equipment(self, direction):
        #print(f"Distribution de l'équipement sélectionné: {direction}")
        self.drawing_canvas.distribute_selected_equipment(direction)

    #------------- fonction liée au changement de mode Equipement/Connexion

    def on_panel_mode_changed(self, mode):
        """Callback quand le mode du panneau gauche change"""
        #print(f"🔄 Mode du panneau changé vers: {mode}")
        
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
        #print(f"🔌 Mode de connexion changé vers: {connection_mode}")
        
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
        #print("🏁 Création de polyligne terminée - reset du panneau connexion")
        
        # Remettre le panneau connexion en mode normal
        connection_panel = self.Left_panel.get_connection_panel()
        if connection_panel.is_in_create_mode():
            connection_panel.reset_mode()
            #print("✅ Bouton 'Création de tuyau' remis à l'état normal")

        #Marquer le projet comme modifié
        self.file_manager.set_modified(True)
        self.update_window_title()
        
        # Mettre à jour la barre de statut
        self.statusBar().showMessage("Mode: Sélection")

    def on_ports_visibility_changed(self, visible):
        """Callback quand l'utilisateur change la visibilité des ports"""
        #print(f"🎛️ Demande de changement visibilité ports: {visible}")
        self.drawing_canvas.set_connected_ports_visibility(visible)
        
        status_msg = "affichés" if visible else "cachés"
        self.statusBar().showMessage(f"Ports connectés {status_msg}", 2000)

    #fonctions liées au changement des propriétés des éleéments via le panel de droite
    def update_equipment_properties(self, equipment_id, updated_properties):
        """Met à jour les propriétés d'un équipement donné"""
        #print(f"🔄 Mise à jour des propriétés de {equipment_id}: {updated_properties}")
        self.drawing_canvas.update_equipment_properties(equipment_id=equipment_id, new_properties=updated_properties)

        #Marquer le projet comme modifié
        self.file_manager.set_modified(True)
        self.update_window_title()

    #fonction liées au changement des proporiétés des pipes via le panel de droite
    def update_pipe_properties(self, pipe_id, updated_properties):
        """Met à jour les propriétés d'un tuyau donné"""
        #print(f"🔄 Mise à jour des propriétés du tuyau {pipe_id}: {updated_properties}")
        self.drawing_canvas.update_pipe_properties(pipe_id=pipe_id, new_properties=updated_properties)

        #Marquer le projet comme modifié
        self.file_manager.set_modified(True)
        self.update_window_title()

    '''def on_pipe_properties_requested(self):
        """Callback pour fournir les propriétés du tuyau au canvas"""
        connection_panel = self.Left_panel.get_connection_panel()
        properties = connection_panel.get_pipe_properties()
        self.drawing_canvas.cached_pipe_properties = properties'''
    
    #------------ fonctions liées aux calculs --------------------------------------------

    def run_simulation(self):
        """Point d'entrée pour la simulation"""
        print("🚀 Lancement de la simulation...")
        success = self.simulation_controller.run_complete_simulation()
        
        if success:
            self.statusBar().showMessage("Simulation terminée avec succès", 5000)
        else:
            self.statusBar().showMessage("Erreur lors de la simulation", 5000)

    #------------ fonctions liées à la gestion des fichiers ------------------------------

    def new_project(self):
        """Crée un nouveau projet"""
        # Vérifier si le projet actuel doit être sauvegardé
        if self.file_manager.is_project_modified():
            response = self.ask_save_before_action("Nouveau projet")
            if response == QMessageBox.Cancel:
                return
            elif response == QMessageBox.Save:
                if not self.save_project():
                    return  # Annuler si la sauvegarde échoue
        
        # Nettoyer le canvas
        self.drawing_canvas.clear_all_equipment()
        
        # Réinitialiser le gestionnaire de fichiers
        self.file_manager = FlowCADFileManager()
        
        # Mettre à jour l'interface
        self.update_window_title()
        self.statusBar().showMessage("Nouveau projet créé", 3000)
        
        print("📄 Nouveau projet créé")
    
    def open_project(self):
        """Ouvre un projet existant"""
        # Vérifier si le projet actuel doit être sauvegardé
        if self.file_manager.is_project_modified():
            response = self.ask_save_before_action("Ouverture de fichier")
            if response == QMessageBox.Cancel:
                return
            elif response == QMessageBox.Save:
                if not self.save_project():
                    return
        
        # Dialog d'ouverture de fichier
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un projet FlowCAD",
            "",  # Répertoire par défaut
            f"Fichiers FlowCAD (*{FlowCADFileManager.DEFAULT_EXTENSION});;Tous les fichiers (*.*)"
        )
        
        if file_path:
            success = self.file_manager.load_project(file_path, self.drawing_canvas)
            
            if success:
                self.update_window_title()
                self.statusBar().showMessage(f"Projet ouvert : {file_path}", 5000)
                
                # Ajuster la vue pour voir tous les équipements
                self.drawing_canvas.fit_all_equipment()
                
                print(f"📂 Projet ouvert : {file_path}")
            else:
                QMessageBox.critical(
                    self, 
                    "Erreur",
                    f"Impossible d'ouvrir le fichier :\n{file_path}"
                )
    
    def save_project(self) -> bool:
        """Sauvegarde le projet actuel"""
        current_path = self.file_manager.get_current_file_path()
        
        if current_path is None:
            # Premier enregistrement : demander où sauvegarder
            return self.save_project_as()
        else:
            # Sauvegarder dans le fichier existant
            metadata = {
                "author": "FlowCAD User",  # TODO: Récupérer des paramètres utilisateur
                "description": f"Projet {self.file_manager.get_project_name()}"
            }
            
            success = self.file_manager.save_project(
                self.drawing_canvas, 
                current_path, 
                metadata
            )
            
            if success:
                self.update_window_title()
                self.statusBar().showMessage(f"Projet sauvegardé", 3000)
                print(f"💾 Projet sauvegardé : {current_path}")
                return True
            else:
                QMessageBox.critical(
                    self,
                    "Erreur de sauvegarde", 
                    "Impossible de sauvegarder le projet"
                )
                return False
    
    def save_project_as(self) -> bool:
        """Sauvegarde le projet avec un nouveau nom"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le projet FlowCAD",
            f"nouveau_projet{FlowCADFileManager.DEFAULT_EXTENSION}",
            f"Fichiers FlowCAD (*{FlowCADFileManager.DEFAULT_EXTENSION});;Tous les fichiers (*.*)"
        )
        
        if file_path:
            metadata = {
                "author": "FlowCAD User",
                "description": f"Projet FlowCAD"
            }
            
            success = self.file_manager.save_project(
                self.drawing_canvas, 
                file_path, 
                metadata
            )
            
            if success:
                self.update_window_title()
                self.statusBar().showMessage(f"Projet sauvegardé : {file_path}", 5000)
                print(f"💾 Projet sauvegardé sous : {file_path}")
                return True
            else:
                QMessageBox.critical(
                    self,
                    "Erreur de sauvegarde",
                    f"Impossible de sauvegarder le fichier :\n{file_path}"
                )
                return False
        
        return False  # L'utilisateur a annulé
    
    def ask_save_before_action(self, action_name: str) -> int:
        """
        Demande à l'utilisateur s'il veut sauvegarder avant une action
        
        Returns:
            QMessageBox.Save, QMessageBox.Discard, ou QMessageBox.Cancel
        """
        project_name = self.file_manager.get_project_name()
        
        return QMessageBox.question(
            self,
            action_name,
            f"Le projet '{project_name}' a été modifié.\n"
            f"Voulez-vous sauvegarder les modifications avant de continuer ?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
    
    def update_window_title(self):
        """Met à jour le titre de la fenêtre"""
        project_name = self.file_manager.get_project_name()
        modified_indicator = " *" if self.file_manager.is_project_modified() else ""
        
        self.setWindowTitle(f"FlowCAD - {project_name}{modified_indicator}")

def main():
    """Point d'entrée de l'application GUI"""
    app = QApplication(sys.argv)
    
    window = FlowCADMainWindow()
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())