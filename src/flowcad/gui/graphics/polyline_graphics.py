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

#from .equipment_graphics import PortGraphicsItem, PortConnectionStatus

# =============================================================================
# CLASSE PRINCIPALE POUR UNE POLYLIGNE GRAPHIQUE
# =============================================================================

class PolylineGraphicsItem(QGraphicsPathItem):
    """Élément graphique représentant une polyligne de connexion"""
    
    def __init__(self, points: List[QPointF], start_port=None, end_port=None):
        super().__init__()
        
        self.points = points.copy()
        self.start_port = start_port
        self.end_port = end_port
        self.control_points: List[PolylineControlPoint] = []
        
        # Style de la polyligne
        self.normal_pen = QPen(QColor(70, 130, 180), 3)  # Bleu acier, épaisseur 3
        self.selected_pen = QPen(QColor(255, 140, 0), 4)  # Orange, épaisseur 4
        self.hover_pen = QPen(QColor(30, 144, 255), 4)   # Bleu dodger
        
        # Configuration
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)  # Au-dessus de la grille, sous les équipements
        
        # Créer le chemin initial
        self.update_path()
        self.setPen(self.normal_pen)
        
        # Créer les points de contrôle (cachés initialement)
        self.create_control_points()
    
    def update_path(self):
        """Met à jour le chemin graphique à partir des points"""
        if len(self.points) < 2:
            return
        
        path = QPainterPath()
        path.moveTo(self.points[0])
        
        for i in range(1, len(self.points)):
            path.lineTo(self.points[i])
        
        self.setPath(path)
    
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
            self.start_port.set_connection_status(PortConnectionStatus.FREE)
        if self.end_port:
            self.end_port.set_connection_status(PortConnectionStatus.FREE)
    
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
        self.setZValue(10)  # Au-dessus de la polyligne
        
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

def create_polyline_from_ports(start_port, end_port, intermediate_points: List[QPointF] = None) -> PolylineGraphicsItem:
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
        
        return [start, middle, end]