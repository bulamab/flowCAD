# =============================================================================
# src/flowcad/gui/components/ribbon_toolbar.py
# =============================================================================
"""
Ribbon Toolbar simple pour FlowCAD - Démarrage avec rotation
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                            QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class RibbonToolbar(QWidget):
    """Barre d'outils style ribbon simple"""
    
    # Signaux émis par la toolbar
    rotate_equipment = pyqtSignal()  # Signal pour rotation 90°
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setFixedHeight(80)  # Hauteur fixe du ribbon
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du ribbon"""
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(15)
        
        # === GROUPE TRANSFORMATION ===
        transform_group = self.create_tool_group(
            "Transformation", 
            [
                ("↻ Rotation\n90°", self.on_rotate_clicked, "Faire pivoter l'équipement sélectionné de 90°")
            ]
        )
        main_layout.addWidget(transform_group)
        
        # === ESPACEMENT FLEXIBLE ===
        main_layout.addStretch()  # Pousse le contenu vers la gauche
        
        # === ZONE D'INFORMATIONS (OPTIONNEL) ===
        info_label = QLabel("FlowCAD v0.1.0")
        info_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        info_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main_layout.addWidget(info_label)
    
    def create_tool_group(self, title: str, tools: list) -> QFrame:
        """
        Crée un groupe d'outils avec titre
        
        Args:
            title: Nom du groupe
            tools: Liste de tuples (nom_bouton, callback, tooltip)
        """
        
        # Conteneur du groupe
        group_frame = QFrame()
        group_frame.setFrameStyle(QFrame.Box)
        group_frame.setLineWidth(1)
        group_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                margin: 2px;
            }
        """)
        
        # Layout vertical pour le groupe
        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(8, 5, 8, 5)
        group_layout.setSpacing(3)
        
        # Titre du groupe
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 8, QFont.Bold))
        title_label.setStyleSheet("color: #495057; border: none;")
        group_layout.addWidget(title_label)
        
        # Layout horizontal pour les boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        
        # Créer les boutons
        for tool_name, callback, tooltip in tools:
            button = self.create_tool_button(tool_name, callback, tooltip)
            buttons_layout.addWidget(button)
        
        group_layout.addLayout(buttons_layout)
        
        return group_frame
    
    def create_tool_button(self, text: str, callback, tooltip: str) -> QPushButton:
        """Crée un bouton d'outil standardisé"""
        
        button = QPushButton(text)
        button.setFixedSize(60, 45)  # Bouton carré
        button.setToolTip(tooltip)
        
        # Style du bouton
        button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: #ffffff;
                font-size: 9px;
                font-weight: bold;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 1px solid #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                border: 1px solid #6c757d;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #adb5bd;
                border: 1px solid #e9ecef;
            }
        """)
        
        # Connecter le callback
        button.clicked.connect(callback)
        
        return button
    
    def on_rotate_clicked(self):
        """Callback du bouton rotation"""
        print("🔄 Bouton rotation cliqué")
        self.rotate_equipment.emit()
    
    def set_tool_enabled(self, tool_name: str, enabled: bool):
        """Active/désactive un outil (pour plus tard)"""
        # Pour l'instant, on peut désactiver manuellement
        # Plus tard, on pourra faire une recherche par nom
        pass

# =============================================================================
# src/flowcad/gui/graphics/equipment_graphics.py - AJOUT DE LA ROTATION
# =============================================================================
"""
Ajout de la fonctionnalité de rotation aux équipements
"""

class EquipmentGraphicsItem(QGraphicsItem):
    """Équipement avec support de la rotation - Version étendue"""
    
    def __init__(self, equipment_id: str, equipment_def: dict, svg_path: str = None):
        # ... code existant ...
        super().__init__()
        
        self.equipment_id = equipment_id
        self.equipment_def = equipment_def
        self.svg_path = svg_path
        
        self.width = 80
        self.height = 60
        
        # ✅ NOUVEAU : Angle de rotation (en degrés)
        self.rotation_angle = 0
        
        # ... reste du code d'initialisation existant ...
        
        self.svg_item = None
        self.text_item = None
        self.ports = {}
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        self.selection_pen = QPen(QColor(0, 120, 255), 2, Qt.DashLine)
        self.selection_brush = QBrush(QColor(0, 120, 255, 30))
        
        self.create_components()
        self.create_ports()
    
    def rotate_90_degrees(self):
        """Fait pivoter l'équipement de 90° dans le sens horaire"""
        
        print(f"🔄 Rotation de {self.equipment_id}: {self.rotation_angle}° → {self.rotation_angle + 90}°")
        
        # ✅ MÉTHODE 1 : Rotation avec transform Qt
        current_rotation = self.rotation()
        new_rotation = current_rotation + 90
        
        # Normaliser l'angle (0-360°)
        if new_rotation >= 360:
            new_rotation -= 360
        
        self.setRotation(new_rotation)
        self.rotation_angle = new_rotation
        
        # ✅ MÉTHODE ALTERNATIVE : Ajuster les positions des ports après rotation
        # (Si vous voulez garder les ports alignés sur la grille)
        # self.reposition_ports_after_rotation()
        
        # Forcer la mise à jour de l'affichage
        self.update()
        
        print(f"✅ Nouvelle rotation: {self.rotation_angle}°")
    
    def reposition_ports_after_rotation(self):
        """Repositionne les ports après rotation (optionnel)"""
        
        # Cette méthode permet de garder les ports "alignés" sur les côtés
        # même après rotation, au lieu de les faire tourner avec l'équipement
        
        for port_id, port in self.ports.items():
            # Récupérer la configuration du port
            ports_config = self.equipment_def.get('ports', {})
            if port_id not in ports_config:
                continue
            
            original_position = ports_config[port_id].get('position', 'left')
            
            # Calculer la nouvelle position selon la rotation
            new_position = self.get_rotated_position(original_position, self.rotation_angle)
            
            # Repositionner le port
            self.position_port(port, new_position)
    
    def get_rotated_position(self, original_position: str, angle: float) -> str:
        """Calcule la nouvelle position d'un port après rotation"""
        
        position_map = {'left': 0, 'top': 90, 'right': 180, 'bottom': 270}
        reverse_map = {0: 'left', 90: 'top', 180: 'right', 270: 'bottom'}
        
        if original_position not in position_map:
            return original_position
        
        original_angle = position_map[original_position]
        new_angle = (original_angle + angle) % 360
        
        return reverse_map.get(new_angle, original_position)
    
    def get_rotation_angle(self) -> float:
        """Retourne l'angle de rotation actuel"""
        return self.rotation_angle
    
    def set_rotation_angle(self, angle: float):
        """Définit l'angle de rotation"""
        self.rotation_angle = angle % 360
        self.setRotation(self.rotation_angle)
        self.update()
    
    # ... reste du code existant (boundingRect, paint, itemChange, etc.) ...

# =============================================================================
# src/flowcad/gui/components/drawing_canvas.py - AJOUT GESTION ROTATION
# =============================================================================
"""
Modification du DrawingCanvas pour gérer la rotation
"""

class DrawingCanvas(QGraphicsView):
    """Canvas avec support de la rotation d'équipements"""
    
    # ... code existant ...
    
    def rotate_selected_equipment(self):
        """Fait pivoter les équipements sélectionnés de 90°"""
        
        selected_items = self.scene.selectedItems()
        rotated_count = 0
        
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                item.rotate_90_degrees()
                rotated_count += 1
        
        if rotated_count > 0:
            print(f"🔄 {rotated_count} équipement(s) tourné(s)")
            return True
        else:
            print("❌ Aucun équipement sélectionné pour la rotation")
            return False
    
    def keyPressEvent(self, event):
        """Ajout du raccourci clavier pour la rotation"""
        
        if event.key() == Qt.Key_R:
            # Touche R : Rotation
            self.rotate_selected_equipment()
        
        elif event.key() == Qt.Key_Delete:
            # Supprimer les éléments sélectionnés
            self.delete_selected_items()
        
        # ... autres raccourcis existants ...
        
        else:
            super().keyPressEvent(event)

# =============================================================================
# src/flowcad/gui/main_window.py - INTÉGRATION DU RIBBON
# =============================================================================
"""
Modification de la main window pour intégrer le ribbon
"""

class FlowCADMainWindow(QMainWindow):
    """Main window avec ribbon toolbar"""
    
    def setup_ui(self):
        """Setup UI modifié avec ribbon"""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ✅ AJOUTER LE RIBBON TOOLBAR EN HAUT
        self.ribbon_toolbar = RibbonToolbar(self)
        main_layout.addWidget(self.ribbon_toolbar)
        
        # Layout horizontal pour les panneaux (code existant)
        panels_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(panels_splitter)
        
        # Panneaux existants...
        self.equipment_panel = EquipmentPanel(self)
        panels_splitter.addWidget(self.equipment_panel)
        
        self.drawing_canvas = DrawingCanvas(self)
        panels_splitter.addWidget(self.drawing_canvas)
        
        self.properties_panel = PropertiesPanel(self)
        panels_splitter.addWidget(self.properties_panel)
        
        panels_splitter.setSizes([280, 840, 280])
        
        # Connecter le loader
        self.drawing_canvas.set_equipment_loader(self.equipment_loader)
    
    def connect_signals(self):
        """Connexion des signaux - version étendue"""
        
        # ... signaux existants ...
        
        # ✅ NOUVEAU : Signaux du ribbon toolbar
        self.ribbon_toolbar.rotate_equipment.connect(self.on_rotate_equipment_requested)
    
    def on_rotate_equipment_requested(self):
        """Callback du bouton rotation du ribbon"""
        
        success = self.drawing_canvas.rotate_selected_equipment()
        
        if success:
            self.update_status_message("Équipement(s) tourné(s) de 90°")
            self.set_project_modified(True)  # Marquer le projet comme modifié
        else:
            self.update_status_message("Sélectionnez un équipement pour le faire pivoter")

# =============================================================================
# TEST DE LA ROTATION
# =============================================================================

def test_rotation():
    """Test de la fonctionnalité de rotation"""
    import sys
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # Fenêtre de test
    window = QWidget()
    window.setWindowTitle("Test Rotation - FlowCAD")
    window.setGeometry(100, 100, 800, 600)
    
    layout = QVBoxLayout(window)
    
    # Ribbon toolbar
    ribbon = RibbonToolbar()
    layout.addWidget(ribbon)
    
    # Canvas simple pour test
    from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
    
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setSceneRect(0, 0, 600, 400)
    layout.addWidget(view)
    
    # Créer un équipement de test
    equipment_def = {'display_name': 'Test Rotation', 'color': '#FF6B6B'}
    equipment = EquipmentGraphicsItem("TEST_001", equipment_def)
    equipment.setPos(300, 200)
    scene.addItem(equipment)
    
    # Connecter le bouton rotation
    def rotate_test():
        selected_items = scene.selectedItems()
        for item in selected_items:
            if hasattr(item, 'rotate_90_degrees'):
                item.rotate_90_degrees()
        
        if not selected_items:
            print("Sélectionnez l'équipement d'abord !")
    
    ribbon.rotate_equipment.connect(rotate_test)
    
    window.show()
    
    print("Instructions:")
    print("1. Cliquez sur l'équipement pour le sélectionner")
    print("2. Cliquez sur le bouton '↻ Rotation 90°' dans le ribbon")
    print("3. L'équipement devrait pivoter de 90°")
    print("4. Ou utilisez la touche 'R' comme raccourci")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_rotation()