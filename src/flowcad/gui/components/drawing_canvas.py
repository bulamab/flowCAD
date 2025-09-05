# =============================================================================
# src/flowcad/gui/components/drawing_canvas.py - Version adaptée
# =============================================================================
"""
Zone de dessin principale avec support drag & drop d'équipements hydrauliques
"""

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem, 
                            QApplication, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush, QWheelEvent, QContextMenuEvent
import json
from typing import Dict, List, Optional, Tuple

# Import de la nouvelle classe graphique
from ..graphics.equipment_graphics import (EquipmentGraphicsItem, PortGraphicsItem, 
                                        PortConnectionStatus, PortVisualState, EquipmentGraphicsFactory)

from ..graphics.polyline_graphics import (PolylineGraphicsItem, PolylineControlPoint, create_polyline_from_ports)

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

        #liste des équipements sélectionnés, dans l'ordre
        self.selected_equipments: List[str] = []
        
        # Loader pour les chemins SVG (à connecter avec votre loader)
        self.equipment_loader = None  # Sera défini par la main_window
        
        # Mode d'interaction
        self.interaction_mode = "select"  # "select", "create_polyline", "draw"
    
        # Variables pour la création de polylignes
        self.current_polyline = None  # Polyligne en cours de création
        self.polyline_points = []     # Points de la polyligne en cours
        self.start_port = None        # Port de départ
        self.preview_line = None      # Ligne de prévisualisation
        self.is_creating_polyline = False  # Flag de création active

        # Liste des polylignes créées
        self.polylines: List[PolylineGraphicsItem] = []
        
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
    # GESTION DE LA SOURIS
    # =============================================================================
    def mousePressEvent(self, event):
        """Gestion des clics avec détection prioritaire des ports"""
        
        if self.interaction_mode == "create_polyline" and self.is_creating_polyline:
            if event.button() == Qt.LeftButton:
                
                # ⚠️ CORRECTION: Chercher spécifiquement un port
                scene_pos = self.mapToScene(event.pos())
                items_at_pos = self.scene.items(scene_pos)
                
                # Filtrer pour ne garder que les ports
                port_item = None
                for item in items_at_pos:
                    if isinstance(item, PortGraphicsItem):
                        port_item = item
                        break
                
                if port_item:
                    # Clic sur un port - terminer la polyligne
                    print(f"🎯 Port détecté: {port_item.port_id}")
                    self.handle_port_click_for_polyline(port_item)
                    event.accept()
                    return
                else:
                    # Pas de port - ajouter un point intermédiaire
                    constrained_pos = self.apply_orthogonal_constraint(scene_pos)
                    self.add_polyline_point(constrained_pos)
                    event.accept()
                    return
            
            elif event.button() == Qt.RightButton:
                self.cancel_polyline_creation()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Mouvement de souris pour prévisualisation"""
        
        if self.interaction_mode == "create_polyline" and self.is_creating_polyline:
            scene_pos = self.mapToScene(event.pos())
            
            # Appliquer les contraintes orthogonales
            constrained_pos = self.apply_orthogonal_constraint(scene_pos)
            
            # Mettre à jour la prévisualisation
            self.update_polyline_preview(constrained_pos)
            event.accept()
            return
        
        super().mouseMoveEvent(event)

    def apply_orthogonal_constraint(self, pos: QPointF) -> QPointF:
        """Applique les contraintes orthogonales (mouvement H ou V uniquement)"""
        
        if not self.polyline_points:
            return pos
        
        last_point = self.polyline_points[-1]
        
        # Calculer les distances horizontale et verticale
        dx = abs(pos.x() - last_point.x())
        dy = abs(pos.y() - last_point.y())
        
        # Garder la direction dominante
        if dx > dy:
            # Mouvement horizontal dominant
            return QPointF(pos.x(), last_point.y())
        else:
            # Mouvement vertical dominant
            return QPointF(last_point.x(), pos.y())
        
    def handle_port_click_for_polyline(self, port):
        """Gère les clics sur ports - MISE À JOUR avec contraintes"""
        print
        if not self.start_port:
            # Premier clic - démarrer la polyligne
            if not port.can_connect():
                print(f"❌ Port {port.port_id} ne peut pas être utilisé comme point de départ")
                return
            
            self.start_port = port
            port.set_connection_status(PortConnectionStatus.RESERVED)
            port.set_visual_state(PortVisualState.SELECTED)
            
            # Position de départ
            start_pos = port.scenePos()
            self.polyline_points = [start_pos]
            
            # Créer la polyligne de prévisualisation
            self.current_polyline = PolylineGraphicsItem([start_pos, start_pos])
            self.current_polyline.setFlag(QGraphicsPathItem.ItemIsSelectable, False)
            self.current_polyline.setAcceptHoverEvents(False)
            self.current_polyline.setZValue(-10)  # Très en arrière-plan

            self.scene.addItem(self.current_polyline)
            
            # Activer le mode création
            self.is_creating_polyline = True
            
            print(f"🚀 Début de polyligne depuis {port.port_id}")
            print("   💡 Clic gauche = ajouter point, Clic droit = annuler")
            
            # Mettre à jour le statut
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage(
                    "Création polyligne: Clic gauche = point, clic droit = annuler, clic sur port = terminer"
                )
            
        else:
            # Clic sur un port pour terminer
            if port == self.start_port:
                print("❌ Ne peut pas connecter un port à lui-même")
                return
            
            if not port.can_connect():
                print(f"❌ Port {port.port_id} ne peut pas être utilisé comme point d'arrivée")
                return
            
            # Ajouter le point final
            end_pos = port.scenePos()
            
            # Appliquer contrainte orthogonale pour le dernier segment
            if len(self.polyline_points) > 1:
                constrained_end = self.apply_orthogonal_constraint(end_pos)
                self.polyline_points.append(constrained_end)
            
            self.polyline_points.append(end_pos)
            
            print(f"🏁 Fin de polyligne sur {port.port_id}")
            
            # Finaliser la polyligne
            self.finalize_polyline(port)

    def add_polyline_point(self, pos: QPointF):
        """Ajoute un point intermédiaire à la polyligne en cours"""
        
        if not self.is_creating_polyline:
            return
        
        self.polyline_points.append(pos)
        
        # Mettre à jour la polyligne de prévisualisation
        if self.current_polyline:
            self.current_polyline.points = self.polyline_points.copy()
            # Ajouter un point temporaire pour la suite
            self.current_polyline.points.append(pos)
            self.current_polyline.update_path()
        
        print(f"📍 Point ajouté: ({pos.x():.1f}, {pos.y():.1f})")
        print(f"   Total points: {len(self.polyline_points)}")

    def update_polyline_preview(self, pos: QPointF):
        """Met à jour la prévisualisation de la polyligne"""
        
        if not self.current_polyline or not self.is_creating_polyline:
            return
        
        # Copier les points existants
        preview_points = self.polyline_points.copy()
        preview_points.append(pos)
        
        # Mettre à jour la polyligne de prévisualisation
        self.current_polyline.points = preview_points
        self.current_polyline.update_path()

    def finalize_polyline(self, end_port):
        """Finalise la création de la polyligne"""
        
        if len(self.polyline_points) < 2:
            print("❌ Pas assez de points pour créer une polyligne")
            self.cancel_polyline_creation()
            return
        
        # Supprimer la polyligne de prévisualisation
        if self.current_polyline:
            self.scene.removeItem(self.current_polyline)
            self.current_polyline = None
        
        # Créer la polyligne finale
        final_polyline = PolylineGraphicsItem(
            self.polyline_points, 
            self.start_port, 
            end_port
        )
        
        self.scene.addItem(final_polyline)
        self.polylines.append(final_polyline)
        
        # Marquer les ports comme connectés
        self.start_port.set_connection_status(PortConnectionStatus.CONNECTED)
        end_port.set_connection_status(PortConnectionStatus.CONNECTED)
        
        # États visuels normaux
        self.start_port.set_visual_state(PortVisualState.NORMAL)
        end_port.set_visual_state(PortVisualState.NORMAL)
        
        print(f"✅ Polyligne créée avec {len(self.polyline_points)} points")
        
        # Réinitialiser
        self.reset_polyline_creation()
        
        # Retourner au mode sélection
        self.set_interaction_mode("select")

    def reset_polyline_creation(self):
        """Remet à zéro les variables de création"""
        self.current_polyline = None
        self.polyline_points = []
        self.start_port = None
        self.is_creating_polyline = False

    def cancel_polyline_creation(self):
        """Annule la création de polyligne - MISE À JOUR"""

        # ⚠️ GUARD: Ne rien faire si pas de création en cours
        if not self.is_creating_polyline and not self.start_port:
            print("🔍 cancel_polyline_creation appelé mais pas de création en cours")
            return
        
        # Libérer le port de départ
        if self.start_port:
            self.start_port.set_connection_status(PortConnectionStatus.DISCONNECTED)
            self.start_port.set_visual_state(PortVisualState.NORMAL)
        
        # Supprimer la polyligne de prévisualisation
        if self.current_polyline:
            self.scene.removeItem(self.current_polyline)
        
        # Réinitialiser
        self.reset_polyline_creation()
        
        print("❌ Création de polyligne annulée")
        
        # Retourner au mode sélection
        self.set_interaction_mode("select")

    def remove_polyline(self, polyline: PolylineGraphicsItem):
        """Supprime une polyligne et libère ses ports"""
        
        # Libérer les ports connectés
        if polyline.start_port:
            polyline.start_port.set_connection_status(PortConnectionStatus.FREE)
        if polyline.end_port:
            polyline.end_port.set_connection_status(PortConnectionStatus.FREE)
        
        # Supprimer de la scène
        self.scene.removeItem(polyline)
        
        # Supprimer de notre liste
        if polyline in self.polylines:
            self.polylines.remove(polyline)
        
        print("🗑️ Polyligne supprimée")
    
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
        #afficher tous les éléments sélectionnés
        eq_id_in_list = []
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                print(f"📍 Équipement sélectionné: {item.equipment_id}")
                self.equipment_selected.emit(item.equipment_id)
                #mettre à jour la liste des équipements sélectionnés
                eq_id_in_list.append(item.equipment_id)

                if item.equipment_id not in self.selected_equipments:
                    self.selected_equipments.append(item.equipment_id)

            elif isinstance(item, PortGraphicsItem):
                parent_eq = item.parent_equipment
                if parent_eq:
                    print(f"🔌 Port sélectionné: {item.port_id} de {parent_eq.equipment_id}")
                    self.port_selected.emit(parent_eq.equipment_id, item.port_id)
        #retire les éléments de la liste self.selected_equipments qui ne sont plus dans

        print(f"eq_id_in_lists: {eq_id_in_list}")
        print(f"Équipements sélectionnés: {self.selected_equipments}")
        #retire les éléments de la liste self.selected_equipments qui ne sont plus dans eq_id_in_list
        self.selected_equipments = [eq_id for eq_id in self.selected_equipments if eq_id in eq_id_in_list]

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
    
    def rotate_selected_equipment(self, angle):
        """Fait pivoter les équipements sélectionnés d'un certain angle"""
        print(f"Rotation de l'équipement sélectionné de {angle}°")
        selected_items = self.scene.selectedItems()
        rotated_count = 0
        
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                item.set_rotation_angle(angle)
                rotated_count += 1
        
        if rotated_count > 0:
            print(f"🔄 {rotated_count} équipement(s) tourné(s)")
            return True
        else:
            print("❌ Aucun équipement sélectionné pour la rotation")
            return False
        
    def mirror_selected_equipment(self, direction):
        """Fait un miroir des équipements sélectionnés dans la direction spécifiée"""
        print(f"Miroir de l'équipement sélectionné: {direction}")
        selected_items = self.scene.selectedItems()
        mirrored_count = 0

        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                item.set_mirror_direction(direction)
                mirrored_count += 1

        if mirrored_count > 0:
            print(f"🔄 {mirrored_count} équipement(s) mis en miroir")
            return True
        else:
            print("❌ Aucun équipement sélectionné pour le miroir")
            return False
        
    def align_selected_equipment(self, direction):
        print(f"Alignement de l'équipement sélectionné: {direction}")
        #selected_items = self.scene.selectedItems()

        selected_equipments = [self.equipment_items[eq_id] for eq_id in self.selected_equipments if eq_id in self.equipment_items]

        #si au moins deux éléments, prendre la position du dernier élément
        if len(selected_equipments) >= 2:
            last_item = selected_equipments[-1]
            last_pos = last_item.pos()
            #si alignement horizontal
            if direction == "v":
                for item in selected_equipments[:-1]:
                    item.setPos(item.pos().x(), last_pos.y())
            elif direction == "h":
                for item in selected_equipments[:-1]:
                    item.setPos(last_pos.x(), item.pos().y())

    def distribute_selected_equipment(self, direction):
        print(f"Distribution de l'équipement sélectionné: {direction}")

        #la liste des éléments sélectionnés
        selected_equipments = [self.equipment_items[eq_id] for eq_id in self.selected_equipments if eq_id in self.equipment_items]
        if len(selected_equipments) < 3:
            print("❌ Pas assez d'équipements sélectionnés pour distribuer")
            return False

        #Si distrbution horizontale
        if direction == "h":
            xmin = min(item.pos().x() for item in selected_equipments)
            xmax = max(item.pos().x() for item in selected_equipments)
            spacing = (xmax - xmin) / (len(selected_equipments) - 1)
            for i, item in enumerate(selected_equipments):
                item.setPos(xmin + i * spacing, item.pos().y())
        elif direction == "v":
            ymin = min(item.pos().y() for item in selected_equipments)
            ymax = max(item.pos().y() for item in selected_equipments)
            spacing = (ymax - ymin) / (len(selected_equipments) - 1)
            for i, item in enumerate(selected_equipments):
                item.setPos(item.pos().x(), ymin + i * spacing)

        print(f"🔄 {len(selected_equipments)} équipement(s) distribués")
        # Mettre à jour l'affichage
        self.update()

    #=========================================================================
    #fonctions liées aux connections

    def set_interaction_mode(self, mode):
        """Change le mode d'interaction du canvas"""
        print(f"🎯 Mode d'interaction changé vers: {mode}")
        
        old_mode = self.interaction_mode
        self.interaction_mode = mode
        
        # Nettoyer l'ancien mode
        if old_mode == "create_polyline":
            self.cancel_polyline_creation()
        
        # Configurer le nouveau mode
        if mode == "create_polyline":
            self.setCursor(Qt.CrossCursor)
            # Changer la couleur des ports libres pour les rendre plus visibles
            self.highlight_available_ports(True)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.highlight_available_ports(False)

    def highlight_available_ports(self, highlight=True):
        """Met en évidence les ports disponibles pour connexion"""
        for equipment_item in self.equipment_items.values():
            for port in equipment_item.get_all_ports():
                if port.can_connect():  # Utilise la nouvelle méthode
                    if highlight:
                        port.set_visual_state(PortVisualState.PREVIEW)
                    else:
                        port.set_visual_state(PortVisualState.NORMAL)

    
    '''
    def handle_port_click_for_polyline(self, port):
        """Gère les clics sur ports en mode création de polyligne - VERSION MISE À JOUR"""
        
        if not self.start_port:
            # Premier clic - démarrer la polyligne
            if not port.can_connect():
                print(f"❌ Port {port.port_id} ne peut pas être utilisé comme point de départ")
                return
            
            self.start_port = port
            port.set_connection_status(PortConnectionStatus.RESERVED)  # Réserver temporairement
            port.set_visual_state(PortVisualState.SELECTED)
            
            # Position de départ en coordonnées de scène
            start_pos = port.scenePos()
            self.polyline_points = [start_pos]
            
            print(f"🚀 Début de polyligne depuis {port.port_id}")
            print(f"   Position: {start_pos.x():.1f}, {start_pos.y():.1f}")
            
        else:
            # Deuxième clic (ou plus) - terminer la polyligne
            if port == self.start_port:
                print("❌ Ne peut pas connecter un port à lui-même")
                return
            
            if not port.can_connect():
                print(f"❌ Port {port.port_id} ne peut pas être utilisé comme point d'arrivée")
                return
            
            end_pos = port.scenePos()
            self.polyline_points.append(end_pos)
            
            print(f"🏁 Fin de polyligne sur {port.port_id}")
            print(f"   Position: {end_pos.x():.1f}, {end_pos.y():.1f}")
            
            # Créer la polyligne finale
            #self.create_final_polyline()
            
            # Marquer les ports comme connectés
            self.start_port.set_connection_status(PortConnectionStatus.CONNECTED)
            port.set_connection_status(PortConnectionStatus.CONNECTED)
            
            # États visuels normaux
            self.start_port.set_visual_state(PortVisualState.NORMAL)
            port.set_visual_state(PortVisualState.NORMAL)
            
            # Réinitialiser
            self.start_port = None
            self.polyline_points = []
            '''
    
'''def cancel_polyline_creation(self):
    """Annule la création de polyligne en cours - VERSION MISE À JOUR"""
    
    # Libérer le port de départ s'il était réservé
    if self.start_port:
        self.start_port.set_connection_status(PortConnectionStatus.FREE)
        self.start_port.set_visual_state(PortVisualState.NORMAL)
    
    # Nettoyer les éléments graphiques
    if self.current_polyline:
        self.scene.removeItem(self.current_polyline)
        self.current_polyline = None
    
    if self.preview_line:
        self.scene.removeItem(self.preview_line)
        self.preview_line = None
    
    self.polyline_points = []
    self.start_port = None
    print("❌ Création de polyligne annulée")'''

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