# =============================================================================
# src/flowcad/gui/graphics/polyline_graphics.py
# =============================================================================
"""
Classes graphiques pour représenter les polylignes de connexion sur le canvas
"""

from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor, QBrush
from typing import List, Optional
from enum import Enum

from .equipment_graphics import PortGraphicsItem, PortConnectionStatus
from .pipe_style_manager import pipe_style_manager


'''class MovementType(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical" 
    DIAGONAL = "diagonal"'''

# =============================================================================
# CLASSE PRINCIPALE POUR UNE POLYLIGNE GRAPHIQUE
# =============================================================================

class PolylineGraphicsItem(QGraphicsPathItem):
    """Élément graphique représentant une polyligne de connexion"""
    
    def __init__(self, points: List[QPointF], start_port=None, end_port=None, pipe_id = None):
        super().__init__()
        
        self.pipe_id = pipe_id  # Identifiant unique de la polyligne
        self.pipe_def = {}  # Définition de la polyligne (à compléter plus tard)
        self.points = points.copy()
        self.start_port = start_port
        self.end_port = end_port
        self.control_points: List[PolylineControlPoint] = []

        #liaison avec l'équipement existant
        self.register_with_connected_equipment()

        #va chercher les valeurs par défaut de pipe_style_manager       
        normal_style = pipe_style_manager.get_pipe_style('normal')
        selected_style = pipe_style_manager.get_pipe_style('selected') 
        hover_style = pipe_style_manager.get_pipe_style('hover')
        
        # Style de la polyligne
        self.normal_pen = QPen(QColor(normal_style['stroke']), float(normal_style['stroke-width']))
        self.selected_pen = QPen(QColor(selected_style['stroke']), float(selected_style['stroke-width']))
        self.hover_pen = QPen(QColor(hover_style['stroke']), float(hover_style['stroke-width']))
        
        # Configuration
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)  # Au-dessus de la grille, sous les équipements
        
        # Créer le chemin initial
        self.update_path()
        self.setPen(self.normal_pen)
        
        # Créer les points de contrôle (cachés initialement)
        self.create_control_points()

        self.pipe_def["properties"] = {
            "length_m": "10",
            "diameter_m": "0.2",
            "roughness_mm": "0.1"
        }
        self.pipe_def["results"] = {
            "flow_rate": "0.0",
            "headloss": "0.0",
            "velocity": "0.0",
            "pressure_1": "0.0",
            "head_1": "0.0",
            "pressure_2": "0.0",
            "head_2": "0.0",
            "total_headloss": "0.0"
        }

    def update_path(self):
        """Met à jour le chemin graphique à partir des points"""
        if len(self.points) < 2:
            return
        
        # Invalider l'ancienne zone avant modification
        if self.scene():
            old_rect = self.mapRectToScene(self.boundingRect())
            old_rect = old_rect.adjusted(-5, -5, 5, 5)  # Petite marge
            self.scene().update(old_rect)

        path = QPainterPath()
        path.moveTo(self.points[0])
        
        for i in range(1, len(self.points)):
            path.lineTo(self.points[i])
        
        self.setPath(path)

        # Invalider la nouvelle zone après modification
        if self.scene():
            new_rect = self.mapRectToScene(self.boundingRect())
            new_rect = new_rect.adjusted(-5, -5, 5, 5)  # Petite marge
            self.scene().update(new_rect)
    
    def create_control_points(self):
        """Crée les points de contrôle pour l'édition"""
        # Nettoyer les anciens points de contrôle
        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points.clear()
        
        # Créer les nouveaux points de contrôle (sauf premier et dernier)
        for i in range(1, len(self.points) - 1):
            control_point = PolylineControlPoint(i, self)
            control_point.setPos(self.points[i])
            control_point.setParentItem(self)
            self.control_points.append(control_point)
    
    def add_point(self, point: QPointF):
        """Ajoute un point à la polyligne"""
        self.points.append(point)
        self.update_path()
        self.create_control_points()
    
    def insert_point(self, index: int, point: QPointF):
        """Insère un point à une position donnée"""
        if 0 <= index <= len(self.points):
            self.points.insert(index, point)
            self.update_path()
            self.create_control_points()
    
    def remove_point(self, index: int):
        """Supprime un point (sauf premier et dernier)"""
        if 1 <= index < len(self.points) - 1:
            self.points.pop(index)
            self.update_path()
            self.create_control_points()
    
    def set_last_point(self, point: QPointF):
        """Modifie le dernier point (pour la prévisualisation)"""
        if len(self.points) > 0:
            self.points[-1] = point
            self.update_path()
    
    def show_control_points(self, show=True):
        """Affiche ou cache les points de contrôle"""
        for cp in self.control_points:
            cp.setVisible(show)
    
    def get_port_connections(self):
        """Retourne les ports connectés par cette polyligne"""
        return (self.start_port, self.end_port)
    
    def disconnect_ports(self):
        """Déconnecte les ports associés à cette polyligne"""
        if self.start_port:
            self.start_port.set_connection_status(PortConnectionStatus.DISCONNECTED)
        if self.end_port:
            self.end_port.set_connection_status(PortConnectionStatus.DISCONNECTED)

    # =============================================================================
    # GESTION DES ÉVÉNEMENTS
    # =============================================================================
    
    def hoverEnterEvent(self, event):
        """Survol de la polyligne"""
        self.setPen(self.hover_pen)
        # Afficher les points de contrôle au survol
        self.show_control_points(True)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol"""
        pen = self.selected_pen if self.isSelected() else self.normal_pen
        self.setPen(pen)
        # Cacher les points de contrôle si pas sélectionné
        if not self.isSelected():
            self.show_control_points(False)
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Changement d'état de l'item"""
        if change == QGraphicsPathItem.ItemSelectedChange:
            pen = self.selected_pen if value else self.normal_pen
            self.setPen(pen)
            # Afficher les points de contrôle si sélectionné
            self.show_control_points(value)
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Clic sur la polyligne"""
        if event.button() == Qt.LeftButton:
            print(f"🔗 Polyligne sélectionnée")
        super().mousePressEvent(event)

    def register_with_connected_equipment(self):
        """S'enregistre auprès des équipements connectés pour recevoir les notifications"""
        if self.start_port and self.start_port.parent_equipment:
            self.start_port.parent_equipment.add_connected_polyline(self)
        
        if self.end_port and self.end_port.parent_equipment:
            self.end_port.parent_equipment.add_connected_polyline(self)
        
        print(f"🔗 Polyligne enregistrée auprès des équipements connectés")
    
    def unregister_from_connected_equipment(self):
        """Se désenregistre des équipements connectés"""
        if self.start_port and self.start_port.parent_equipment:
            self.start_port.parent_equipment.remove_connected_polyline(self)
        
        if self.end_port and self.end_port.parent_equipment:
            self.end_port.parent_equipment.remove_connected_polyline(self)
        
        print(f"🔗 Polyligne désenregistrée des équipements connectés")
    
    def update_connection_points(self):
        """Met à jour les points en maintenant l'alignement orthogonal"""
        if not self.start_port or not self.end_port:
            print("⚠️ Impossible de mettre à jour : ports manquants")
            return
        
        # Sauvegarder l'ancienne zone avant modification
        old_bounding_rect = self.boundingRect()
        old_scene_rect = self.mapRectToScene(old_bounding_rect)

        # Obtenir les nouvelles positions des ports
        new_start_pos = self.start_port.scenePos()
        new_end_pos = self.end_port.scenePos()
        
        # Vérifier quel port a bougé
        old_start_pos = self.points[0]
        old_end_pos = self.points[-1]
        
        start_moved = self.has_moved_significantly(old_start_pos, new_start_pos)
        end_moved = self.has_moved_significantly(old_end_pos, new_end_pos)
        
        if not start_moved and not end_moved:
            return
        
        print(f"🔄 Mise à jour polyligne: start_moved={start_moved}, end_moved={end_moved}")
        
        # Mettre à jour les points concernés
        if start_moved:
            self.update_start_point_and_adjacent(new_start_pos)
        
        if end_moved:
            self.update_end_point_and_adjacent(new_end_pos)
        
        # Redessiner
        self.update_path()
        self.update_control_points_positions()

        # Invalider l'ancienne ET la nouvelle zone
        new_bounding_rect = self.boundingRect()
        new_scene_rect = self.mapRectToScene(new_bounding_rect)
        
        # Combiner les deux zones avec une marge de sécurité
        combined_rect = old_scene_rect.united(new_scene_rect)
        margin = 10  # Marge de sécurité
        combined_rect = combined_rect.adjusted(-margin, -margin, margin, margin)
        
        # Forcer le repaint de cette zone
        if self.scene():
            self.scene().update(combined_rect)
            print(f"🎨 Zone repaint: {combined_rect.width():.0f}x{combined_rect.height():.0f}")


    def has_moved_significantly(self, old_pos, new_pos, threshold=1.0):
        """Vérifie si un point a bougé de manière significative"""
        dx = abs(new_pos.x() - old_pos.x())
        dy = abs(new_pos.y() - old_pos.y())
        return dx > threshold or dy > threshold
    
    def update_start_point_and_adjacent(self, new_start_pos):
        """Met à jour le point de départ et son point adjacent"""
        
        # Mettre à jour le point de départ
        old_start = self.points[0]
        self.points[0] = new_start_pos
        
        # S'il y a un point adjacent (index 1)
        if len(self.points) >= 2:
            adjacent_point = self.points[1]
            
            # Déterminer quelle coordonnée était alignée avec l'ancien port
            same_x = abs(adjacent_point.x() - old_start.x()) < 1.0
            same_y = abs(adjacent_point.y() - old_start.y()) < 1.0
            
            if same_x:
                # Le point était aligné horizontalement → maintenir X identique
                self.points[1] = QPointF(new_start_pos.x(), adjacent_point.y())
                print(f"📐 Point adjacent au start: alignement X maintenu ({new_start_pos.x():.1f})")
                
            elif same_y:
                # Le point était aligné verticalement → maintenir Y identique  
                self.points[1] = QPointF(adjacent_point.x(), new_start_pos.y())
                print(f"📐 Point adjacent au start: alignement Y maintenu ({new_start_pos.y():.1f})")
                
            else:
                print(f"⚠️ Point adjacent au start: pas d'alignement détecté")

    def update_end_point_and_adjacent(self, new_end_pos):
        """Met à jour le point de fin et son point adjacent"""
        
        # Mettre à jour le point de fin
        old_end = self.points[-1]
        self.points[-1] = new_end_pos
        
        # S'il y a un point adjacent (avant-dernier)
        if len(self.points) >= 2:
            adjacent_point = self.points[-2]
            
            # Déterminer quelle coordonnée était alignée avec l'ancien port
            same_x = abs(adjacent_point.x() - old_end.x()) < 1.0
            same_y = abs(adjacent_point.y() - old_end.y()) < 1.0
            
            if same_x:
                # Le point était aligné horizontalement → maintenir X identique
                self.points[-2] = QPointF(new_end_pos.x(), adjacent_point.y())
                print(f"📐 Point adjacent au end: alignement X maintenu ({new_end_pos.x():.1f})")
                
            elif same_y:
                # Le point était aligné verticalement → maintenir Y identique
                self.points[-2] = QPointF(adjacent_point.x(), new_end_pos.y())
                print(f"📐 Point adjacent au end: alignement Y maintenu ({new_end_pos.y():.1f})")
                
            else:
                print(f"⚠️ Point adjacent au end: pas d'alignement détecté")

    '''def debug_point_alignment(self):
        """Debug pour vérifier les alignements"""
        print("🔍 DEBUG alignements:")
        for i, point in enumerate(self.points):
            print(f"  Point {i}: ({point.x():.1f}, {point.y():.1f})")
        
        if len(self.points) >= 2:
            # Vérifier alignement start avec point 1
            start_point = self.points[0]
            second_point = self.points[1]
            same_x = abs(start_point.x() - second_point.x()) < 1.0
            same_y = abs(start_point.y() - second_point.y()) < 1.0
            print(f"  Start-Point1: same_X={same_x}, same_Y={same_y}")
            
            # Vérifier alignement end avec avant-dernier
            if len(self.points) >= 2:
                end_point = self.points[-1]
                before_end = self.points[-2]
                same_x = abs(end_point.x() - before_end.x()) < 1.0
                same_y = abs(end_point.y() - before_end.y()) < 1.0
                print(f"  End-BeforeEnd: same_X={same_x}, same_Y={same_y}")'''

    '''def get_movement_type(self, old_pos, new_pos):
        """Détermine le type de mouvement (horizontal, vertical, diagonal)"""
        delta_x = abs(new_pos.x() - old_pos.x())
        delta_y = abs(new_pos.y() - old_pos.y())
        
        if delta_x > delta_y * 2:
            return "horizontal"
        elif delta_y > delta_x * 2:
            return "vertical"
        else:
            return "diagonal"'''
    
    '''def reroute_simple_line(self, start_pos: QPointF, end_pos: QPointF):
        """Re-route une ligne simple en forme de L orthogonal"""
        
        # Choisir la direction selon la distance dominante ou préférences
        dx = abs(end_pos.x() - start_pos.x())
        dy = abs(end_pos.y() - start_pos.y())
        
        if dx > dy:
            # Mouvement horizontal dominant : horizontal puis vertical
            middle_point = QPointF(end_pos.x(), start_pos.y())
        else:
            # Mouvement vertical dominant : vertical puis horizontal
            middle_point = QPointF(start_pos.x(), end_pos.y())
        
        self.points = [start_pos, middle_point, end_pos]
        print(f"  📐 Ligne simple re-routée: {len(self.points)} points")'''
    
    '''def reroute_l_shape(self, start_pos: QPointF, end_pos: QPointF, 
                       start_delta: QPointF, end_delta: QPointF):
        """Re-route une polyligne en L en préservant l'intention originale"""
        
        old_middle = self.points[1]
        
        # Analyser l'orientation actuelle de la polyligne
        current_pattern = self.analyze_path_pattern()
        
        if current_pattern == "H-V":  # Horizontal puis Vertical
            # Préserver le pattern : ajuster le point de coude
            if abs(start_delta.x()) > 0.1:  # Le start a bougé horizontalement
                # Ajuster le X du point de coude
                new_middle = QPointF(old_middle.x() + start_delta.x(), old_middle.y())
            else:
                # Le end a bougé, ajuster selon le mouvement
                new_middle = QPointF(old_middle.x(), end_pos.y())
            
        elif current_pattern == "V-H":  # Vertical puis Horizontal  
            # Préserver le pattern : ajuster le point de coude
            if abs(start_delta.y()) > 0.1:  # Le start a bougé verticalement
                # Ajuster le Y du point de coude
                new_middle = QPointF(old_middle.x(), old_middle.y() + start_delta.y())
            else:
                # Le end a bougé, ajuster selon le mouvement
                new_middle = QPointF(end_pos.x(), old_middle.y())
        
        else:
            # Pattern non reconnu : créer un nouveau L optimal
            self.reroute_simple_line(start_pos, end_pos)
            return
        
        self.points = [start_pos, new_middle, end_pos]
        print(f"  📐 Forme L re-routée: pattern {current_pattern}")'''
    
    '''def reroute_complex_path(self, start_pos: QPointF, end_pos: QPointF,
                            start_delta: QPointF, end_delta: QPointF):
        """Re-route une polyligne complexe avec multiple segments"""
        
        # Stratégie : ajuster les points en préservant l'orthogonalité
        new_points = [start_pos]
        
        # Analyser quel port a bougé le plus
        start_movement = abs(start_delta.x()) + abs(start_delta.y())
        end_movement = abs(end_delta.x()) + abs(end_delta.y())
        
        if start_movement > end_movement:
            # Le start a plus bougé : ajuster depuis le début
            self.adjust_path_from_start(new_points, start_delta, end_pos)
        else:
            # Le end a plus bougé : ajuster depuis la fin
            self.adjust_path_from_end(new_points, end_delta, end_pos)
        
        new_points.append(end_pos)
        self.points = new_points
        print(f"  📐 Chemin complexe re-routé: {len(self.points)} points")'''
    
    '''def analyze_path_pattern(self) -> str:
        """Analyse le pattern de la polyligne actuelle"""
        if len(self.points) < 3:
            return "DIRECT"
        
        # Analyser le premier segment
        first_segment = QPointF(self.points[1].x() - self.points[0].x(),
                               self.points[1].y() - self.points[0].y())
        
        if abs(first_segment.x()) > abs(first_segment.y()):
            return "H-V"  # Commence horizontal
        else:
            return "V-H"  # Commence vertical'''
    
    '''def adjust_path_from_start(self, new_points: List[QPointF], delta: QPointF, end_pos: QPointF):
        """Ajuste le chemin en partant du début"""
        
        # Stratégie simple : propager le delta sur les premiers points
        for i in range(1, len(self.points) - 1):
            old_point = self.points[i]
            
            # Déterminer quelle coordonnée ajuster selon l'orientation du segment précédent
            prev_point = new_points[-1] if new_points else self.points[i-1]
            
            # Si le segment précédent était horizontal, ajuster X
            if abs(old_point.x() - prev_point.x()) > abs(old_point.y() - prev_point.y()):
                new_point = QPointF(old_point.x() + delta.x(), old_point.y())
            else:
                # Le segment précédent était vertical, ajuster Y
                new_point = QPointF(old_point.x(), old_point.y() + delta.y())
            
            new_points.append(new_point)
    
    def adjust_path_from_end(self, new_points: List[QPointF], delta: QPointF, end_pos: QPointF):
        """Ajuste le chemin en partant de la fin (plus complexe)"""
        
        # Pour l'instant, utiliser une stratégie simple
        # TODO: Implémenter un algorithme plus sophistiqué si nécessaire
        
        # Copier tous les points intermédiaires sans modification
        for i in range(1, len(self.points) - 1):
            new_points.append(self.points[i])
        
        print(f"  ⚠️ Ajustement depuis la fin : algorithme simple utilisé")'''
    
    def update_control_points_positions(self):
        """Met à jour les positions des points de contrôle"""
        for i, control_point in enumerate(self.control_points):
            if i + 1 < len(self.points):  # Points intermédiaires seulement
                control_point.setPos(self.points[i + 1])
    
    def destroy(self):
        """Nettoie la polyligne avant destruction"""
        self.unregister_from_connected_equipment()
        
        # Nettoyer les points de contrôle
        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points.clear()

    def update_properties(self, new_def: dict):
        """Met à jour les propriétés de l'équipement"""
        #seules les propriétés editables sont mises à jour
        self.pipe_def['properties'].update(new_def)
        print(f"🔧 Propriétés mises à jour pour {self.pipe_id}: {new_def}")

# =============================================================================
# Fonctions utilitaires pour la gestion des polylignes
# =============================================================================

'''def calculate_optimal_orthogonal_path(start: QPointF, end: QPointF, 
                                    preference: str = "auto") -> List[QPointF]:
    """Calcule un chemin orthogonal optimal entre deux points"""
    
    dx = end.x() - start.x()
    dy = end.y() - start.y()
    
    # Cas trivial : déjà aligné
    if abs(dx) < 0.1:  # Verticalement aligné
        return [start, end]
    elif abs(dy) < 0.1:  # Horizontalement aligné
        return [start, end]
    
    # Choisir la direction selon les préférences ou la distance
    if preference == "horizontal_first":
        middle = QPointF(end.x(), start.y())
        return [start, middle, end]
    elif preference == "vertical_first":
        middle = QPointF(start.x(), end.y())
        return [start, middle, end]
    else:  # "auto"
        # Choisir selon la distance dominante
        if abs(dx) > abs(dy):
            middle = QPointF(end.x(), start.y())  # Horizontal d'abord
        else:
            middle = QPointF(start.x(), end.y())  # Vertical d'abord
        return [start, middle, end]'''

'''def is_point_orthogonal_to_segment(point: QPointF, seg_start: QPointF, seg_end: QPointF) -> bool:
    """Vérifie si un point forme un angle droit avec un segment"""
    
    # Vecteur du segment
    seg_vec = QPointF(seg_end.x() - seg_start.x(), seg_end.y() - seg_start.y())
    
    # Vecteur vers le point
    point_vec = QPointF(point.x() - seg_end.x(), point.y() - seg_end.y())
    
    # Produit scalaire (doit être proche de 0 pour un angle droit)
    dot_product = seg_vec.x() * point_vec.x() + seg_vec.y() * point_vec.y()
    
    return abs(dot_product) < 1.0  # Tolérance pour les erreurs de calcul'''

'''def validate_orthogonal_path(points: List[QPointF]) -> bool:
    """Vérifie qu'un chemin est entièrement orthogonal"""
    
    if len(points) < 2:
        return True
    
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        
        # Chaque segment doit être soit horizontal soit vertical
        dx = abs(p2.x() - p1.x())
        dy = abs(p2.y() - p1.y())
        
        # Un des deux doit être proche de 0
        if not (dx < 0.1 or dy < 0.1):
            print(f"⚠️ Segment non-orthogonal détecté: {i}->{i+1}")
            return False
    
    return True'''

'''def optimize_orthogonal_path(points: List[QPointF]) -> List[QPointF]:
    """Optimise un chemin orthogonal en supprimant les points redondants"""
    
    if len(points) <= 2:
        return points
    
    optimized = [points[0]]
    
    for i in range(1, len(points) - 1):
        prev_point = optimized[-1]
        current_point = points[i]
        next_point = points[i + 1]
        
        # Vérifier si le point courant est nécessaire
        # (pas sur la même ligne que le précédent et le suivant)
        
        # Direction du segment précédent
        prev_is_horizontal = abs(current_point.y() - prev_point.y()) < 0.1
        
        # Direction du segment suivant  
        next_is_horizontal = abs(next_point.y() - current_point.y()) < 0.1
        
        # Garder le point seulement s'il y a changement de direction
        if prev_is_horizontal != next_is_horizontal:
            optimized.append(current_point)
        else:
            print(f"📐 Point redondant supprimé à l'index {i}")
    
    optimized.append(points[-1])
    return optimized'''

# =============================================================================
# CLASSE POUR LES POINTS DE CONTRÔLE
# =============================================================================

class PolylineControlPoint(QGraphicsEllipseItem):
    """Point de contrôle pour modifier une polyligne"""
    
    def __init__(self, point_index: int, polyline_item: PolylineGraphicsItem):
        super().__init__(-4, -4, 8, 8)  # Petit cercle de 8px de diamètre
        
        self.point_index = point_index
        self.polyline_item = polyline_item
        self.is_dragging = False
        
        # Style
        self.normal_brush = QBrush(QColor(255, 255, 255))
        self.hover_brush = QBrush(QColor(255, 255, 0))
        self.selected_brush = QBrush(QColor(255, 140, 0))
        
        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor(70, 130, 180), 2))
        
        # Configuration
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(3)  # Au-dessus de la polyligne
        
        # Initialement caché
        self.setVisible(False)
        
        # Curseur de déplacement
        self.setCursor(Qt.SizeAllCursor)
    
    def hoverEnterEvent(self, event):
        """Survol du point de contrôle"""
        self.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol"""
        brush = self.selected_brush if self.isSelected() else self.normal_brush
        self.setBrush(brush)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Début du déplacement"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.setBrush(self.selected_brush)
            print(f"📍 Début déplacement point {self.point_index}")
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Déplacement du point avec contraintes orthogonales"""
        if not self.is_dragging:
            return
        
        # Position actuelle de la souris en coordonnées de scène
        scene_pos = event.scenePos()
        
        # Appliquer les contraintes orthogonales
        constrained_pos = self.apply_orthogonal_constraints(scene_pos)
        
        # Mettre à jour la position du point de contrôle
        parent_pos = self.parentItem().mapFromScene(constrained_pos) if self.parentItem() else constrained_pos
        self.setPos(parent_pos)
        
        # Mettre à jour la polyligne
        if 0 <= self.point_index < len(self.polyline_item.points):
            self.polyline_item.points[self.point_index] = constrained_pos
            self.polyline_item.update_path()
        
        # Pas besoin d'appeler super() car on gère le déplacement manuellement
    
    def mouseReleaseEvent(self, event):
        """Fin du déplacement"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            print(f"📍 Fin déplacement point {self.point_index}")
        super().mouseReleaseEvent(event)
    
    def apply_orthogonal_constraints(self, new_pos: QPointF) -> QPointF:
        """Applique les contraintes orthogonales lors du déplacement"""
        
        points = self.polyline_item.points
        index = self.point_index
        
        if index <= 0 or index >= len(points) - 1:
            return new_pos  # Pas de contraintes pour les points extrêmes
        
        # Points adjacent
        prev_point = points[index - 1]
        next_point = points[index + 1] if index + 1 < len(points) else None
        
        # Calculer les distances à partir du point précédent
        dx = abs(new_pos.x() - prev_point.x())
        dy = abs(new_pos.y() - prev_point.y())
        
        # Mouvement dominant détermine la contrainte
        if dx > dy:
            # Mouvement horizontal : garder Y du point précédent
            constrained_pos = QPointF(new_pos.x(), prev_point.y())
        else:
            # Mouvement vertical : garder X du point précédent
            constrained_pos = QPointF(prev_point.x(), new_pos.y())
        
        return constrained_pos
    
    def itemChange(self, change, value):
        """Changement d'état du point de contrôle"""
        if change == QGraphicsEllipseItem.ItemSelectedChange:
            brush = self.selected_brush if value else self.normal_brush
            self.setBrush(brush)
        return super().itemChange(change, value)

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

'''def create_polyline_from_ports(start_port, end_port, intermediate_points: List[QPointF] = None) -> PolylineGraphicsItem:
    """Crée une polyligne entre deux ports avec points intermédiaires optionnels"""
    
    points = [start_port.scenePos()]
    
    if intermediate_points:
        points.extend(intermediate_points)
    
    points.append(end_port.scenePos())
    
    return PolylineGraphicsItem(points, start_port, end_port)

def calculate_orthogonal_path(start: QPointF, end: QPointF, mode="auto") -> List[QPointF]:
    """Calcule un chemin orthogonal simple entre deux points"""
    
    if mode == "horizontal_first":
        # Segment horizontal puis vertical
        middle = QPointF(end.x(), start.y())
        return [start, middle, end]
    
    elif mode == "vertical_first":
        # Segment vertical puis horizontal
        middle = QPointF(start.x(), end.y())
        return [start, middle, end]
    
    else:  # "auto"
        # Choisir la direction selon la distance dominante
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        
        if dx > dy:
            # Distance horizontale plus grande : horizontal d'abord
            middle = QPointF(end.x(), start.y())
        else:
            # Distance verticale plus grande : vertical d'abord
            middle = QPointF(start.x(), end.y())
        
        return [start, middle, end]'''