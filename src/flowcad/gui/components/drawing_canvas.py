# =============================================================================
# src/flowcad/gui/components/drawing_canvas.py - Version adaptée
# =============================================================================
"""
Zone de dessin principale avec support drag & drop d'équipements hydrauliques
"""

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsItem, 
                            QApplication, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush, QWheelEvent, QContextMenuEvent
import json
from typing import Dict, List, Optional, Tuple

# Import de la nouvelle classe graphique
from ..graphics.equipment_graphics import (EquipmentGraphicsItem, PortGraphicsItem, 
                                         PortStatus, EquipmentGraphicsFactory)

class DrawingCanvas(QGraphicsView):
    """Zone de dessin principale pour FlowCAD"""
    
    # Signaux émis par le canvas
    equipment_dropped = pyqtSignal(str, dict, tuple)  # (equipment_id, equipment_def, position)
    equipment_selected = pyqtSignal(str)              # equipment_id
    equipment_deleted = pyqtSignal(str)               # equipment_id
    port_selected = pyqtSignal(str, str)              # (equipment_id, port_id)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setup_view()
        self.setup_scene()
        
        # Gestion des équipements
        self.equipment_counter = 0
        self.equipment_items: Dict[str, EquipmentGraphicsItem] = {}
        
        # Loader pour les chemins SVG (à connecter avec votre loader)
        self.equipment_loader = None  # Sera défini par la main_window
        
        # Mode d'interaction
        self.interaction_mode = "select"  # "select", "connect", "draw"
        
    def setup_view(self):
        """Configure la vue graphique"""
        
        # Style de base
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Mode de sélection
        self.setDragMode(QGraphicsView.RubberBandDrag)  # Sélection par zone
        
        # Activer le drag & drop
        self.setAcceptDrops(True)
        
        # Activer le zoom avec la molette
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Anti-aliasing pour un rendu plus lisse
        #self.setRenderHint(self.renderHints() | self.renderHints().Antialiasing)
    
    def setup_scene(self):
        """Configure la scène graphique"""
        
        # Créer la scène
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Définir une grande zone de travail
        self.scene.setSceneRect(-1000, -1000, 4000, 4000)
        
        # Connecter les signaux de sélection de la scène
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        # Dessiner la grille de fond
        self.draw_background_grid()
    
    def draw_background_grid(self):
        """Dessine une grille de fond pour faciliter le positionnement"""
        
        scene_rect = self.scene.sceneRect()
        grid_size = 50
        
        # Couleur de grille discrète
        grid_pen = QPen(QColor(230, 230, 230), 0.5)
        
        # Lignes verticales
        x = scene_rect.left()
        while x <= scene_rect.right():
            self.scene.addLine(x, scene_rect.top(), x, scene_rect.bottom(), grid_pen)
            x += grid_size
        
        # Lignes horizontales  
        y = scene_rect.top()
        while y <= scene_rect.bottom():
            self.scene.addLine(scene_rect.left(), y, scene_rect.right(), y, grid_pen)
            y += grid_size
    
    def set_equipment_loader(self, loader):
        """Définit le loader pour obtenir les chemins SVG"""
        self.equipment_loader = loader
    
    # =============================================================================
    # GESTION DU DRAG & DROP
    # =============================================================================
    
    def dragEnterEvent(self, event):
        """Début du drag sur le canvas"""
        if event.mimeData().hasFormat('application/x-flowcad-equipment'):
            print("🎯 Drag détecté sur le canvas")
            event.acceptProposedAction()
            
            # Optionnel : changer le curseur ou afficher un aperçu
            self.setCursor(Qt.CrossCursor)
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Mouvement pendant le drag"""
        if event.mimeData().hasFormat('application/x-flowcad-equipment'):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Fin du drag (sortie du canvas)"""
        self.setCursor(Qt.ArrowCursor)
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        """Drop d'un équipement sur le canvas"""
        if event.mimeData().hasFormat('application/x-flowcad-equipment'):
            
            # Remettre le curseur normal
            self.setCursor(Qt.ArrowCursor)
            
            # Décoder les données de l'équipement
            json_data = event.mimeData().data('application/x-flowcad-equipment').data().decode()
            equipment_data = json.loads(json_data)
            
            equipment_id = equipment_data['equipment_id']
            equipment_def = equipment_data['equipment_def']
            
            # Position du drop en coordonnées de scène
            scene_pos = self.mapToScene(event.pos())
            drop_position = (scene_pos.x(), scene_pos.y())
            
            # Aligner sur la grille (optionnel)
            aligned_pos = self.align_to_grid(scene_pos)
            
            print(f"🎯 Drop de {equipment_id} à la position {aligned_pos.x():.1f}, {aligned_pos.y():.1f}")
            
            # Créer l'équipement sur le canvas
            self.add_equipment(equipment_id, equipment_def, aligned_pos)
            
            # Émettre le signal
            self.equipment_dropped.emit(equipment_id, equipment_def, drop_position)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def align_to_grid(self, pos: QPointF, grid_size: int = 25) -> QPointF:
        """Aligne une position sur la grille"""
        aligned_x = round(pos.x() / grid_size) * grid_size
        aligned_y = round(pos.y() / grid_size) * grid_size
        return QPointF(aligned_x, aligned_y)
    
    # =============================================================================
    # GESTION DES ÉQUIPEMENTS
    # =============================================================================
    
    def add_equipment(self, equipment_type: str, equipment_def: dict, position: QPointF) -> str:
        """Ajoute un équipement sur le canvas"""
        
        # Générer un ID unique pour cette instance
        unique_id = f"{equipment_type}_{self.equipment_counter:03d}"
        self.equipment_counter += 1
        
        # Obtenir le chemin SVG si le loader est disponible
        svg_path = None
        if self.equipment_loader:
            try:
                svg_path = self.equipment_loader.get_svg_path(equipment_type)
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement du SVG pour {equipment_type}: {e}")
        
        # Créer l'élément graphique
        equipment_item = EquipmentGraphicsFactory.create_equipment_graphics(
            unique_id, equipment_def, svg_path
        )
        
        # Positionner l'équipement
        equipment_item.setPos(position)
        
        # Ajouter à la scène
        self.scene.addItem(equipment_item)
        
        # Stocker la référence
        self.equipment_items[unique_id] = equipment_item
        
        # Connecter les signaux des ports (si nécessaire)
        self.connect_equipment_signals(equipment_item)
        
        print(f"✅ Équipement {unique_id} ajouté à {position.x():.1f}, {position.y():.1f}")
        
        return unique_id
    
    def connect_equipment_signals(self, equipment_item: EquipmentGraphicsItem):
        """Connecte les signaux d'un équipement et de ses ports"""
        
        # Pour l'instant, on gère les clics sur ports directement dans PortGraphicsItem
        # Plus tard, on pourra ajouter des signaux personnalisés si nécessaire
        pass
    
    def remove_equipment(self, equipment_id: str) -> bool:
        """Supprime un équipement du canvas"""
        
        if equipment_id in self.equipment_items:
            equipment_item = self.equipment_items[equipment_id]
            
            # Retirer de la scène
            self.scene.removeItem(equipment_item)
            
            # Retirer de notre dictionnaire
            del self.equipment_items[equipment_id]
            
            print(f"🗑️ Équipement {equipment_id} supprimé")
            
            # Émettre le signal
            self.equipment_deleted.emit(equipment_id)
            
            return True
        
        return False
    
    def get_equipment(self, equipment_id: str) -> Optional[EquipmentGraphicsItem]:
        """Récupère un équipement par son ID"""
        return self.equipment_items.get(equipment_id)
    
    def get_all_equipment(self) -> Dict[str, EquipmentGraphicsItem]:
        """Récupère tous les équipements"""
        return self.equipment_items.copy()
    
    def clear_all_equipment(self):
        """Supprime tous les équipements"""
        for equipment_id in list(self.equipment_items.keys()):
            self.remove_equipment(equipment_id)
    
    # =============================================================================
    # GESTION DE LA SÉLECTION
    # =============================================================================
    
    def on_selection_changed(self):
        """Callback quand la sélection change dans la scène"""
        
        selected_items = self.scene.selectedItems()
        
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                print(f"📍 Équipement sélectionné: {item.equipment_id}")
                self.equipment_selected.emit(item.equipment_id)
            
            elif isinstance(item, PortGraphicsItem):
                parent_eq = item.parent_equipment
                if parent_eq:
                    print(f"🔌 Port sélectionné: {item.port_id} de {parent_eq.equipment_id}")
                    self.port_selected.emit(parent_eq.equipment_id, item.port_id)
    
    def select_equipment(self, equipment_id: str):
        """Sélectionne un équipement par programme"""
        equipment_item = self.get_equipment(equipment_id)
        if equipment_item:
            # Désélectionner tout
            self.scene.clearSelection()
            # Sélectionner l'équipement
            equipment_item.setSelected(True)
            # Centrer la vue sur l'équipement
            self.centerOn(equipment_item)
    
    # =============================================================================
    # INTERACTION UTILISATEUR
    # =============================================================================
    
    def wheelEvent(self, event: QWheelEvent):
        """Zoom avec la molette de la souris"""
        
        # Facteur de zoom
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            # Zoom avant
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom arrière
            self.scale(1 / zoom_factor, 1 / zoom_factor)
    
    def keyPressEvent(self, event):
        """Gestion des raccourcis clavier"""
        
        if event.key() == Qt.Key_Delete:
            # Supprimer les éléments sélectionnés
            self.delete_selected_items()
        
        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            # Ctrl+A : Sélectionner tout
            for item in self.scene.items():
                if isinstance(item, EquipmentGraphicsItem):
                    item.setSelected(True)
        
        elif event.key() == Qt.Key_Escape:
            # Échap : Désélectionner tout
            self.scene.clearSelection()
        
        else:
            super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """Supprime les équipements sélectionnés"""
        
        selected_items = self.scene.selectedItems()
        equipment_to_delete = []
        
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                equipment_to_delete.append(item.equipment_id)
        
        # Supprimer les équipements
        for equipment_id in equipment_to_delete:
            self.remove_equipment(equipment_id)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Menu contextuel (clic droit)"""
        
        # Trouver l'item sous la souris
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        
        if isinstance(item, EquipmentGraphicsItem):
            # Menu pour un équipement
            menu = QMenu(self)
            
            # Actions sur l'équipement
            properties_action = menu.addAction("🔧 Propriétés")
            rotate_action = menu.addAction("↻ Rotation 90°")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ Supprimer")
            
            # Exécuter le menu
            action = menu.exec_(event.globalPos())
            
            if action == properties_action:
                print(f"Propriétés de {item.equipment_id}")
                # TODO: Ouvrir le panneau des propriétés
            
            elif action == rotate_action:
                print(f"Rotation de {item.equipment_id}")
                # TODO: Implémenter la rotation
                
            elif action == delete_action:
                self.remove_equipment(item.equipment_id)
        
        else:
            # Menu général du canvas
            menu = QMenu(self)
            
            clear_action = menu.addAction("🗑️ Tout effacer")
            menu.addSeparator()
            fit_action = menu.addAction("🔍 Ajuster la vue")
            
            action = menu.exec_(event.globalPos())
            
            if action == clear_action:
                self.clear_all_equipment()
            elif action == fit_action:
                self.fit_all_equipment()
    
    # =============================================================================
    # UTILITAIRES DE VUE
    # =============================================================================
    
    def fit_all_equipment(self):
        """Ajuste la vue pour voir tous les équipements"""
        if self.equipment_items:
            self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        else:
            # Retour à la vue par défaut
            self.setSceneRect(-500, -500, 1000, 1000)
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
    
    def zoom_to_fit(self):
        """Alias pour fit_all_equipment"""
        self.fit_all_equipment()
    
    def reset_zoom(self):
        """Remet le zoom à 100%"""
        self.resetTransform()
    
    # =============================================================================
    # MÉTHODES POUR L'INTÉGRATION
    # =============================================================================
    
    def get_equipment_count(self) -> int:
        """Retourne le nombre d'équipements sur le canvas"""
        return len(self.equipment_items)
    
    def get_connection_count(self) -> int:
        """Retourne le nombre de connexions (pour plus tard)"""
        # TODO: Implémenter quand on aura les connexions
        return 0
    
    def export_equipment_data(self) -> List[dict]:
        """Exporte les données des équipements (pour sauvegarde)"""
        equipment_data = []
        
        for eq_id, eq_item in self.equipment_items.items():
            pos = eq_item.pos()
            data = {
                'equipment_id': eq_id,
                'equipment_def': eq_item.equipment_def,
                'position': {'x': pos.x(), 'y': pos.y()},
                'ports': {}
            }
            
            # Ajouter l'état des ports
            for port_id, port_item in eq_item.ports.items():
                data['ports'][port_id] = {
                    'status': port_item.status.value
                }
            
            equipment_data.append(data)
        
        return equipment_data

# =============================================================================
# EXEMPLE D'UTILISATION DANS MAIN_WINDOW
# =============================================================================

"""
# Dans votre main_window.py :

class FlowCADMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Créer le canvas
        self.drawing_canvas = DrawingCanvas()
        
        # Connecter votre equipment_loader
        self.drawing_canvas.set_equipment_loader(self.equipment_loader)
        
        # Connecter les signaux
        self.drawing_canvas.equipment_dropped.connect(self.on_equipment_dropped)
        self.drawing_canvas.equipment_selected.connect(self.on_equipment_selected)
        self.drawing_canvas.port_selected.connect(self.on_port_selected)
    
    def on_equipment_dropped(self, equipment_id, equipment_def, position):
        print(f"Nouvel équipement: {equipment_id}")
        self.update_status_message(f"Équipement ajouté: {equipment_def.get('display_name')}")
    
    def on_equipment_selected(self, equipment_id):
        print(f"Équipement sélectionné: {equipment_id}")
        # Mettre à jour le panneau des propriétés
    
    def on_port_selected(self, equipment_id, port_id):
        print(f"Port sélectionné: {port_id} de {equipment_id}")
        # Préparer le mode connexion
"""