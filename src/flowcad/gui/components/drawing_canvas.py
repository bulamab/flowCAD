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
from ..graphics.equipment_graphics import *

from ..graphics.polyline_graphics import *

class DrawingCanvas(QGraphicsView):
    """Zone de dessin principale pour FlowCAD"""
    
    # Signaux émis par le canvas
    equipment_dropped = pyqtSignal(str, dict, tuple)  # (equipment_id, equipment_def, position)
    equipment_selected = pyqtSignal(str)              # equipment_id
    equipment_deleted = pyqtSignal(str)               # equipment_id
    port_selected = pyqtSignal(str, str)              # (equipment_id, port_id)

    #pipe_properties_requested = pyqtSignal()          # Signal émis lorsque les propriétés du tuyau sont demandées
    equipment_properties_requested = pyqtSignal(dict, str)  # Envoie directement les données de l'équipement sélectionné
    pipe_properties_requested = pyqtSignal()  # Demande les propriétés
    pipe_properties_received = pyqtSignal(dict)  # Reçoit les propriétés


    polyline_creation_finished = pyqtSignal()         # Signal émis lorsque la création de la polyligne est terminée

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
        self.cached_pipe_properties = None  # Pour stocker les propriétés du tuyau en cours de création
        self.current_pipe_properties = None  # Pour stocker les propriétés du tuyau en cours de création

        # Variables pour le routage de polylignes
        self.orthogonal_routing_enabled = True
        self.routing_preference = "horizontal_first"  # "auto", "horizontal_first", "vertical_first"
        self.routing_optimization = True  # Supprimer les points redondants
        self.routing_tolerance = 0.1     # Tolérance pour l'orthogonalité

        # Liste des polylignes créées
        self.polyline_counter = 0
        #self.polylines: List[PolylineGraphicsItem] = []
        self.polylines: Dict[str, PolylineGraphicsItem] = {}
        #variables pour la création de polylignes
        self.locked_direction = None        # "horizontal", "vertical", ou None
        self.direction_lock_threshold = 10  # Distance minimale pour verrouiller la direction

        #self.init_pipe_style_sync() #plus besoin, se fait automatiquement
        # Connecter le signal de réception des propriétés
        self.pipe_properties_received.connect(self.on_pipe_properties_received)
        
    # Ajouter des méthodes utilitaires pour les contrôles UI

    def set_pipe_color_theme(self, theme: str):
        """Applique un thème de couleur prédéfini"""
        
        themes = {
            'blue': {
                'normal': '#4682B4',
                'selected': '#FF8C00', 
                'hover': '#1E90FF'
            },
            'green': {
                'normal': '#228B22',
                'selected': '#FF6347',
                'hover': '#32CD32'  
            },
            'red': {
                'normal': '#DC143C',
                'selected': '#FFD700',
                'hover': '#FF1493'
            },
            'purple': {
                'normal': '#9932CC',
                'selected': '#FF69B4',
                'hover': '#DA70D6'
            }
        }
        
        if theme in themes:
            colors = themes[theme]
            self.update_pipe_styles(
                normal_color=colors['normal'],
                selected_color=colors['selected'], 
                hover_color=colors['hover']
            )
            print(f"🎨 Thème '{theme}' appliqué")
        else:
            print(f"⚠️ Thème inconnu: {theme}")

    def get_pipe_style_info(self):
        """Retourne les informations sur les styles actuels"""
        return {
            'normal': pipe_style_manager.get_pipe_style('normal'),
            'selected': pipe_style_manager.get_pipe_style('selected'),
            'hover': pipe_style_manager.get_pipe_style('hover'),
            'cache_size': len(pipe_style_manager.modified_svg_cache)
        }
        
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
            print("🎯 Drop reçu:", equipment_data)
            
            equipment_id = equipment_data['equipment_id']
            equipment_def = equipment_data['equipment_def']
            equipment_properties = equipment_def.get('properties', {})

            # Position du drop en coordonnées de scène
            scene_pos = self.mapToScene(event.pos())
            drop_position = (scene_pos.x(), scene_pos.y())
            
            # Aligner sur la grille (optionnel)
            aligned_pos = self.align_to_grid(scene_pos)

            print(f"🎯 Drop de {equipment_id} à la position {aligned_pos.x():.1f}, {aligned_pos.y():.1f}\nPropriétés de l'équipement: {json.dumps(equipment_properties, indent=2, ensure_ascii=False)}")

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

    #---------------------------------------------------------------------------------
    # Fonctions pour le dessin de tuyau
    #---------------------------------------------------------------------------------

    def apply_orthogonal_constraint(self, pos: QPointF) -> QPointF:
        """Applique les contraintes orthogonales (mouvement H ou V uniquement)"""
        
        if not self.polyline_points:
            return pos
        
        last_point = self.polyline_points[-1]
        
        # Calculer les distances depuis le dernier point
        dx = abs(pos.x() - last_point.x())
        dy = abs(pos.y() - last_point.y())

        # Si aucune direction n'est verrouillée, déterminer la direction
        if self.locked_direction is None:
            
            # Vérifier si on a dépassé le seuil pour verrouiller
            if max(dx, dy) >= self.direction_lock_threshold:
                if dx > dy:
                    self.locked_direction = "horizontal"
                    print(f"🔒 Direction verrouillée: HORIZONTALE")
                else:
                    self.locked_direction = "vertical"
                    print(f"🔒 Direction verrouillée: VERTICALE")
            
            # Pas encore de verrouillage, suivre la direction dominante
            if dx > dy:
                return QPointF(pos.x(), last_point.y())
            else:
                return QPointF(last_point.x(), pos.y())
        
        # Direction verrouillée - appliquer la contrainte
        if self.locked_direction == "horizontal":
            constrained_pos = QPointF(pos.x(), last_point.y())
        else:  # vertical
            constrained_pos = QPointF(last_point.x(), pos.y())
        
        # Vérifier si on revient au point précédent pour déverrouiller
        distance_to_last = self.distance_between_points(pos, last_point)
        if distance_to_last < self.direction_lock_threshold / 2:  # Hysteresis
            self.unlock_direction()
            return pos  # Permettre le mouvement libre près du point de départ
        
        return constrained_pos
    
    def distance_between_points(self, p1: QPointF, p2: QPointF) -> float:
        """Calcule la distance entre deux points"""
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return (dx*dx + dy*dy)**0.5
    
    def unlock_direction(self):
        """Déverrouille la direction et permet un nouveau choix"""
        if self.locked_direction:
            print(f"🔓 Direction déverrouillée (était: {self.locked_direction})")
            self.locked_direction = None
        
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
            rect = port.boundingRect() #le bounding rect
            start_pos = port.scenePos()+rect.center() #le centre du port
            self.polyline_points = [start_pos]
            
            # Réinitialiser le verrouillage pour cette nouvelle polyligne
            self.locked_direction = None

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
            rect = port.boundingRect() #le bounding rect
            end_pos = port.scenePos()+rect.center() #le centre du port

            # Appliquer contrainte orthogonale pour le dernier segment
            if len(self.polyline_points) >= 1:
                constrained_end = self.apply_orthogonal_constraint(end_pos)
                print(f"🔧 Contrainte appliquée au point final: ({constrained_end.x():.1f}, {constrained_end.y():.1f})")

                # Vérifier si on a besoin d'un point intermédiaire
                start_pos = self.polyline_points[0]
                
                # Toujours ajouter le point contraint s'il est différent du point final
                if (abs(constrained_end.x() - end_pos.x()) > 1 or 
                    abs(constrained_end.y() - end_pos.y()) > 1):
                    
                    self.polyline_points.append(constrained_end)
                    print(f"📍 Point intermédiaire ajouté: ({constrained_end.x():.1f}, {constrained_end.y():.1f})")
            
            self.polyline_points.append(end_pos)
            
            print(f"🏁 Fin de polyligne sur {port.port_id}")
            
            # Finaliser la polyligne
            self.finalize_polyline(port)

    def add_polyline_point(self, pos: QPointF):
        """Ajoute un point intermédiaire à la polyligne en cours"""
        
        if not self.is_creating_polyline:
            return
        
        self.polyline_points.append(pos)

        #Réinitialiser le verrouillage pour le prochain segment
        print(f"📍 Point ajouté: ({pos.x():.1f}, {pos.y():.1f})")
        print(f"🔓 Direction réinitialisée pour le prochain segment")
        self.locked_direction = None
        
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

        # Sauvegarder les références
        start_port = self.start_port
        end_port_ref = end_port
        points_copy = self.polyline_points.copy()
        # Ajouter des points si seulement 2 points
        enhanced_points = self.add_intermediate_points_if_needed(points_copy)
                
        # Supprimer la polyligne de prévisualisation
        if self.current_polyline:
            self.scene.removeItem(self.current_polyline)
            self.current_polyline = None

        # Générer un ID unique pour cette instance
        unique_pipe_id = f"pipe_{self.polyline_counter:03d}"
        self.polyline_counter += 1

        # Créer la polyligne finale
        final_polyline = PolylineGraphicsItem(
            enhanced_points, 
            self.start_port, 
            end_port,
            pipe_id=unique_pipe_id
        )
        
        #modifier les propriétés par défaut
        pipe_properties = self.request_pipe_properties()
        print(f"Propriétés du tuyau : {pipe_properties}")
        final_polyline.update_properties(pipe_properties or {})

        self.scene.addItem(final_polyline)
        self.polylines[unique_pipe_id] = final_polyline
        
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

        # Émettre le signal de fin de création
        self.polyline_creation_finished.emit()
        print("📡 Signal polyline_creation_finished émis")

    def add_intermediate_points_if_needed(self, points: List[QPointF]) -> List[QPointF]:
        """Ajoute des points si seulement 2 points"""
        
        if len(points) == 2:
            start_point = points[0]
            end_point = points[1]
            
            # Point au milieu exact
            mid_x = start_point.x() + (end_point.x() - start_point.x()) * 0.5
            mid_y = start_point.y() + (end_point.y() - start_point.y()) * 0.5
            
            # Créer 2 points superposés au milieu
            middle_point1 = QPointF(mid_x, mid_y)
            middle_point2 = QPointF(mid_x, mid_y)
            
            print(f"✅ Ajout de 2 points au milieu: ({mid_x:.1f}, {mid_y:.1f})")
            
            return [start_point, middle_point1, middle_point2, end_point]
        elif len(points) == 3:
            # Nouveau cas : 3 points - dupliquer le point final
            duplicated_end_point = QPointF(points[-1].x(), points[-1].y())
        
            print(f"Ajout d'un point dupliqué à la fin: ({duplicated_end_point.x():.1f}, {duplicated_end_point.y():.1f})")
        
            return points + [duplicated_end_point]

        else:
            return points  # Déjà assez de points



    def reset_polyline_creation(self):
        """Remet à zéro les variables de création"""
        self.current_polyline = None
        self.polyline_points = []
        self.start_port = None
        self.is_creating_polyline = False

        # Déverrouiller la direction
        self.unlock_direction()

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

        # Émettre le signal de fin de création (même en cas d'annulation)
        self.polyline_creation_finished.emit()
        print("📡 Signal polyline_creation_finished émis (annulation)")

    def remove_polyline(self, polyline: PolylineGraphicsItem):
        """Supprime une polyligne et libère ses ports"""
        
        polyline.destroy()  # Désenregistre des équipements

        # Libérer les ports connectés
        if polyline.start_port:
            polyline.start_port.set_connection_status(PortConnectionStatus.DISCONNECTED)
        if polyline.end_port:
            polyline.end_port.set_connection_status(PortConnectionStatus.DISCONNECTED)

        # Supprimer de la scène
        self.scene.removeItem(polyline)
        
        # Supprimer de notre liste
        if polyline in self.polylines:
            self.polylines.remove(polyline)
        
        print("🗑️ Polyligne supprimée")

    def set_direction_lock_threshold(self, threshold: int):
        """Définit le seuil de verrouillage de direction"""
        self.direction_lock_threshold = max(5, threshold)  # Minimum 5 pixels
        print(f"🎛️ Seuil de verrouillage: {self.direction_lock_threshold} pixels")

    def set_orthogonal_routing(self, enabled: bool):
        """Active/désactive le routage orthogonal automatique"""
        self.orthogonal_routing_enabled = enabled
        print(f"📐 Routage orthogonal: {'ON' if enabled else 'OFF'}")
    
    def set_routing_preference(self, preference: str):
        """Définit la préférence de routage : 'auto', 'horizontal_first', 'vertical_first'"""
        if preference in ["auto", "horizontal_first", "vertical_first"]:
            self.routing_preference = preference
            print(f"📐 Préférence de routage: {preference}")
        else:
            print(f"⚠️ Préférence invalide: {preference}")
    
    def toggle_routing_optimization(self):
        """Toggle l'optimisation des chemins"""
        self.routing_optimization = not self.routing_optimization
        print(f"📐 Optimisation des chemins: {'ON' if self.routing_optimization else 'OFF'}")
        return self.routing_optimization

    def request_pipe_properties(self) -> Dict[str, float]:
        """Demande les propriétés du tuyau au panneau de connexion"""
        # Émettre le signal de demande
        self.pipe_properties_requested.emit()
        
        # Retourner les propriétés actuelles (ou valeurs par défaut)
        if self.current_pipe_properties:
            return self.current_pipe_properties
        else:
            # Valeurs par défaut si pas encore reçues
            return {
                "diameter_m": 0.1,
                "length_m": 1.0,
                "roughness_mm": 0.1
            }
    
    def on_pipe_properties_received(self, properties):
        """Callback quand les propriétés du tuyau sont reçues"""
        self.current_pipe_properties = properties
        print(f"Propriétés du tuyau reçues : {properties}")


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

        print(f"✅ Équipement {unique_id} ajouté à {position.x():.1f}, {position.y():.1f} avec définition: {json.dumps(equipment_def, ensure_ascii=False)}")

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

            #supprimer les polylignes associées 
            polylines_to_remove = equipment_item.connected_polylines.copy()
            for polyline in polylines_to_remove:
                self.remove_polyline(polyline)
            
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
    
    def get_pipe(self, pipe_id: str) -> Optional[PolylineGraphicsItem]:
        """Récupère un tuyau par son ID"""
        return self.polylines.get(pipe_id)
    
    def get_all_equipment(self) -> Dict[str, EquipmentGraphicsItem]:
        """Récupère tous les équipements"""
        return self.equipment_items.copy()

    def get_all_polylines(self) -> Dict[str, PolylineGraphicsItem]:
        """Récupère tous les tuyaux"""
        return self.polylines.copy()

    def clear_all_equipment(self):
        """Supprime tous les équipements"""
        for equipment_id in list(self.equipment_items.keys()):
            self.remove_equipment(equipment_id)

    def update_equipment_properties(self, equipment_id: str, new_properties: dict):
        """Met à jour les propriétés d'un équipement"""
        
        equipment_item = self.get_equipment(equipment_id)
        if equipment_item:
            equipment_item.update_properties(new_properties)
            print(f"🔧 Propriétés de {equipment_id} mises à jour: {json.dumps(new_properties, ensure_ascii=False)}")
            return True
        else:
            print(f"⚠️ Équipement {equipment_id} non trouvé pour mise à jour")
            return False

    def update_pipe_properties(self, pipe_id: str, new_properties: dict):
        """Met à jour les propriétés d'un tuyau"""
        pipe_item = self.get_pipe(pipe_id)
        if pipe_item:
            pipe_item.update_properties(new_properties)
            print(f"🔧 Propriétés du tuyau {pipe_id} mises à jour: {json.dumps(new_properties, ensure_ascii=False)}")
            return True
        else:
            print(f"⚠️ Tuyau {pipe_id} non trouvé pour mise à jour")
            return False


    # =============================================================================
    # GESTION DE LA SÉLECTION
    # =============================================================================
    
    def on_selection_changed(self):
        """Callback quand la sélection change dans la scène"""
        
        selected_items = self.scene.selectedItems()

        #gestion de l'affichage des propriétés dans le panneau latéral -----------------------------------
        #propriétés affichées uniquement si 1 élément est sélectionné. si 0 ou plusieurs, panneau vide
        #regarde si il y a un equipement ou un tuyau sélectionné
        equipment_or_pipe_items = [item for item in selected_items if isinstance(item, (EquipmentGraphicsItem, PolylineGraphicsItem))]

        #si un seul équipement sélectionné, affiche ses propriétés
        if len(equipment_or_pipe_items) == 1:
            properties_data = {}
            #si l'équipement est un tuyau
            if isinstance(equipment_or_pipe_items[0], PolylineGraphicsItem):
                pipe = equipment_or_pipe_items[0]
                properties_data = pipe.pipe_def
                properties_data["ID"] = pipe.pipe_id
                properties_data["display_name"] = "Tuyau"
                properties_data["description"] = "Tuyau de connexion"
                properties_data["equipment_class"] = "PipeConnectionEquipment"

                self.equipment_properties_requested.emit(properties_data, "pipe")
            else:  # si l'équipement est un équipement standard
                equipment = equipment_or_pipe_items[0]
                properties_data = equipment.equipment_def
                properties_data["ID"] = equipment.equipment_id
                print(f"📋 Affichage des propriétés de {equipment.equipment_id}")
                self.equipment_properties_requested.emit(properties_data, "equipment")

        #si 0 ou plusieurs, pas de propriétés affichées
        else:  #0 ou plusieurs équipements sélectionnés
            print("📋 Aucune propriété affichée (0 ou plusieurs équipements sélectionnés)")
            self.equipment_properties_requested.emit({}, "none")



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
        pipes_to_delete = []
        print(f"éléments sélectionnés: {selected_items}")

        #la liste des équipements à effacer
        for item in selected_items:
            if isinstance(item, EquipmentGraphicsItem):
                equipment_to_delete.append(item.equipment_id)
        
        #la liste des tuyaux (polylignes) à effacer
        for item in selected_items:
            if isinstance(item, PolylineGraphicsItem):
                pipes_to_delete.append(item)

        # Supprimer les équipements
        for equipment_id in equipment_to_delete:
            self.remove_equipment(equipment_id)


        # Supprimer les tuyaux
        for pipe in pipes_to_delete:
            self.remove_polyline(pipe)

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
            last_pos_center = last_item.center
            #print(f"Position de référence pour l'alignement: {last_pos.x()}, {last_pos.y()}\n")
            #print(f"Dimensions de l'équipement: {last_item.boundingRect().width()} x {last_item.boundingRect().height()}\n")
            #print(f"Centre de l'équipement: {last_item.center.x()}, {last_item.center.y()}\n")
            #si alignement horizontal
            if direction == "v":
                for item in selected_equipments[:-1]:
                    center = item.center
                    item.setPos(item.pos().x(), last_pos.y()-center.y()+last_pos_center.y())
            elif direction == "h":
                for item in selected_equipments[:-1]:
                    center = item.center
                    item.setPos(last_pos.x()-center.x()+last_pos_center.x(), item.pos().y())

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
    #=========================================================================

    def set_interaction_mode(self, mode):
        """Change le mode d'interaction du canvas"""
        print(f"🎯 Mode d'interaction changé vers: {mode}")
        
        old_mode = self.interaction_mode
        self.interaction_mode = mode
        
        # Nettoyer l'ancien mode SEULEMENT si nécessaire
        if old_mode == "create_polyline" and self.is_creating_polyline:  # ← AJOUT DE LA CONDITION
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

    
    
    #----- Pour le visibilité ou non des ports connecté-----------------

    def toggle_connected_ports_visibility(self):
        """Toggle l'affichage des ports connectés"""
        current_state = PortGraphicsItem.get_show_connected_ports()
        new_state = not current_state
        
        PortGraphicsItem.set_show_connected_ports(new_state)
        self.update_all_ports_visibility()
        
        status_msg = "Ports connectés affichés" if new_state else "Ports connectés cachés"
        print(f"👻 {status_msg}")
        return new_state

    def set_connected_ports_visibility(self, visible: bool):
        """Définit l'affichage des ports connectés"""
        PortGraphicsItem.set_show_connected_ports(visible)
        self.update_all_ports_visibility()
        
        status_msg = "affichés" if visible else "cachés"
        print(f"👻 Ports connectés {status_msg}")

    def update_all_ports_visibility(self):
        """Met à jour la visibilité de tous les ports existants"""
        total_ports = 0
        updated_ports = 0
        
        for equipment_item in self.equipment_items.values():
            for port in equipment_item.get_all_ports():
                total_ports += 1
                old_visibility = port.isVisible()
                port.update_visibility()
                if old_visibility != port.isVisible():
                    updated_ports += 1
        
        print(f"🔄 {updated_ports}/{total_ports} ports mis à jour")

    def show_all_ports_temporarily(self, duration_ms: int = 3000):
        """Affiche temporairement tous les ports (pour debug/édition)"""
        
        # Sauvegarder l'état actuel
        original_state = PortGraphicsItem.get_show_connected_ports()
        
        # Afficher tous les ports
        self.set_connected_ports_visibility(True)
        
        # Programmer le retour à l'état original
        if hasattr(self, 'temp_visibility_timer'):
            self.temp_visibility_timer.stop()
        
        from PyQt5.QtCore import QTimer
        self.temp_visibility_timer = QTimer()
        self.temp_visibility_timer.timeout.connect(lambda: self.set_connected_ports_visibility(original_state))
        self.temp_visibility_timer.setSingleShot(True)
        self.temp_visibility_timer.start(duration_ms)
        
        print(f"👁️ Affichage temporaire de tous les ports pendant {duration_ms}ms")

    def get_ports_visibility_info(self):
        """Retourne des statistiques sur la visibilité des ports"""
        total_ports = 0
        visible_ports = 0
        connected_ports = 0
        visible_connected_ports = 0
        
        for equipment_item in self.equipment_items.values():
            for port in equipment_item.get_all_ports():
                total_ports += 1
                if port.isVisible():
                    visible_ports += 1
                if port.connection_status == PortConnectionStatus.CONNECTED:
                    connected_ports += 1
                    if port.isVisible():
                        visible_connected_ports += 1
        
        return {
            'total_ports': total_ports,
            'visible_ports': visible_ports, 
            'connected_ports': connected_ports,
            'visible_connected_ports': visible_connected_ports,
            'global_setting': PortGraphicsItem.get_show_connected_ports()
        }

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