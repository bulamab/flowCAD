# =============================================================================
# src/flowcad/gui/graphics/equipment_graphics.py
# =============================================================================
"""
Classes graphiques pour représenter les équipements hydrauliques sur le canvas
"""

from logging import root
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QBrush, QPen, QPainter
from PyQt5.QtSvg import QGraphicsSvgItem
import os
from enum import Enum
from typing import Dict, List, Optional

import re
import xml.etree.ElementTree as ET

# =============================================================================
# ÉNUMÉRATION POUR L'ÉTAT DES PORTS
# =============================================================================

class PortStatus(Enum):
    """États possibles d'un port hydraulique"""
    DISCONNECTED = "disconnected"    # Port libre
    CONNECTED = "connected"          # Port connecté
    HIGHLIGHTED = "highlighted"      # Port en surbrillance (hover)
    SELECTED = "selected"           # Port sélectionné
    ERROR = "error"                 # Port en erreur

# =============================================================================
# CLASSE POUR UN PORT GRAPHIQUE
# =============================================================================

class PortGraphicsItem(QGraphicsEllipseItem):
    """Élément graphique représentant un port d'équipement"""
    
    # Couleurs selon l'état du port
    PORT_COLORS = {
        PortStatus.DISCONNECTED: "#FF6B6B",     # Rouge : libre
        PortStatus.CONNECTED: "#4ECDC4",        # Vert : connecté
        PortStatus.HIGHLIGHTED: "#FFE066",      # Jaune : survol
        PortStatus.SELECTED: "#FF9FF3",         # Rose : sélectionné
        PortStatus.ERROR: "#FF4757"             # Rouge foncé : erreur
    }
    
    def __init__(self, port_id: str, parent_equipment=None):
        # Cercle de rayon 8 pixels centré sur l'origine
        super().__init__(-8, -8, 16, 16)
        
        self.port_id = port_id
        self.parent_equipment = parent_equipment
        self.status = PortStatus.DISCONNECTED

        self.setAcceptHoverEvents(True)
        
        # Rendre le port sélectionnable mais pas déplaçable individuellement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Style initial
        self.update_appearance()
        
        # Tooltip informatif
        self.setToolTip(f"Port: {port_id}\n")
    
    def update_appearance(self):
        """Met à jour l'apparence selon l'état du port"""
        color = QColor(self.PORT_COLORS[self.status])
        
        # Remplissage
        self.setBrush(QBrush(color))
        
        # Contour plus épais si sélectionné
        pen_width = 3 if self.status == PortStatus.SELECTED else 2
        self.setPen(QPen(Qt.black, pen_width))
    
    def set_status(self, status: PortStatus):
        """Change l'état du port"""
        if self.status != status:
            self.status = status
            self.update_appearance()
    
    def mousePressEvent(self, event):
        """Gestion du clic sur le port"""
        if event.button() == Qt.LeftButton:
            print(f"Port cliqué: {self.port_id} de l'équipement {self.parent_equipment.equipment_id if self.parent_equipment else 'N/A'}")
            
            # Changer l'état pour montrer la sélection
            if self.status != PortStatus.SELECTED:
                self.set_status(PortStatus.SELECTED)
            else:
                self.set_status(PortStatus.DISCONNECTED)
            
            # Empêcher la propagation à l'équipement parent
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Survol du port"""
        if self.status == PortStatus.DISCONNECTED:
            self.set_status(PortStatus.HIGHLIGHTED)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol du port"""
        if self.status == PortStatus.HIGHLIGHTED:
            self.set_status(PortStatus.DISCONNECTED)
        super().hoverLeaveEvent(event)

# =============================================================================
# CLASSE PRINCIPALE POUR UN ÉQUIPEMENT GRAPHIQUE
# =============================================================================

class EquipmentGraphicsItem(QGraphicsItem):
    """Élément graphique complet représentant un équipement hydraulique avec ses ports"""
    
    def __init__(self, equipment_id: str, equipment_def: dict, svg_path: str = None):
        super().__init__()
        
        self.equipment_id = equipment_id
        self.equipment_def = equipment_def
        self.svg_path = svg_path
        
        # Dimensions de base de l'équipement
        self.width = 80
        self.height = 60
        self.item_scale = 1.0

        # Composants graphiques
        self.svg_item: Optional[QGraphicsSvgItem] = None
        self.ports: Dict[str, PortGraphicsItem] = {}
        self.ports_infos: List = []
        
        # Rendre l'équipement déplaçable et sélectionnable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Activer la détection de survol
        self.setAcceptHoverEvents(True)
        
        # Créer les composants
        self.create_components()
        self.create_ports()
    
    def create_components(self):
        """Crée les composants visuels de base"""
        
        # 1. Icône SVG ou fallback
        if self.svg_path and os.path.exists(self.svg_path):

            #extrait les informations du SVG
            self.ports_infos = self.read_ports_from_svg(self.svg_path)
            self.svg_item = QGraphicsSvgItem(self.svg_path)
            self.svg_item.setParentItem(self)
            print(f"dimensions: {self.svg_item.boundingRect().width()} x {self.svg_item.boundingRect().height()}")
            # Redimensionner le SVG
            self.item_scale = min(self.width / self.svg_item.boundingRect().width(),
                                  self.height / self.svg_item.boundingRect().height())
            self.svg_item.setScale(self.item_scale)

    #Lit le nombre de ports et leur position en fonction des informations contenues dans le SVG
    def read_ports_from_svg(self, svg_path: str) -> List[dict]:

        #ouvre le fichier SVG
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        #liste des ports
        ports = []

        #parse le contenu SVG pour extraire les informations des ports
        root = ET.fromstring(svg_content)

        # Extraire les dimensions du SVG
        width = float(root.get('width'))
        height = float(root.get('height'))
        viewBox = root.get('viewBox')
        min_x, min_y, vb_width, vb_height = map(float, viewBox.split())
        print(f"SVG dimensions: width={width}, height={height}, viewbox width={vb_width}, height={vb_height}")

        # Chercher tous les éléments avec un attribut id
        for element in root.iter() :
            element_id = element.get('id', '')
        
            # Vérifier si l'id contient "Port" suivi d'un nombre
            match = re.search(r'Port(\d+)', element_id, re.IGNORECASE)
        
            if match:
                numero_port = int(match.group(1))
            
                # Extraire les coordonnées cx et cy
                cx = element.get('cx')
                cy = element.get('cy')
            
                if cx is not None and cy is not None:
                    ports.append({
                        'port': numero_port,
                        'x': float(cx)/vb_width*width,
                        'y': float(cy)/vb_height*height
                    })

        #trier les ports par numéro
        ports.sort(key=lambda x: x['port'])

        #afficher les ports
        for port in ports:
            print(f"Port {port['port']}: ({port['x']}, {port['y']})")

        return ports

    def create_ports(self):
        """Crée les ports selon les valeurs lues dans le SVG"""
        for port_info in self.ports_infos:
            x = port_info['x']*self.item_scale
            y = port_info['y']*self.item_scale
            self.create_port(f"P{port_info['port']}", x, y)


    def create_port(self, port_id: str, x: float, y: float):
        """Crée un port individuel"""
        

        # Créer le port graphique
        port_item = PortGraphicsItem(port_id, parent_equipment=self)
        port_item.setParentItem(self)

        port_item.setPos(x, y)
        
        # Stocker le port
        self.ports[port_id] = port_item
 
    
    def boundingRect(self) -> QRectF:
        """Définit la zone de collision/sélection complète"""
        
        # Zone principale de l'équipement
        equipment_rect = QRectF(0, 0, self.width, self.height)
        
        # Inclure les ports (avec une marge pour faciliter la sélection)
        port_margin = 12
        for port in self.ports.values():
            port_rect = port.boundingRect()
            port_rect.translate(port.pos())
            port_rect.adjust(-port_margin, -port_margin, port_margin, port_margin)
            equipment_rect = equipment_rect.united(port_rect)
        
        return equipment_rect
    
    def paint(self, painter: QPainter, option, widget=None):
        """Dessine l'équipement (fallback si pas de SVG)"""
        
        # Si pas de SVG, dessiner un rectangle coloré
        if not self.svg_item:
            color = QColor(self.equipment_def.get('color', '#666666'))
            
            painter.fillRect(0, 0, self.width, self.height, color)
            painter.setPen(QPen(Qt.black, 2))
            painter.drawRect(0, 0, self.width, self.height)
            
            # Dessiner un "?" au centre
            painter.setPen(QPen(Qt.white))
            painter.drawText(QRectF(0, 0, self.width, self.height), Qt.AlignCenter, "?")
    
    def mousePressEvent(self, event):
        """Gestion des clics sur l'équipement"""
        
        # Vérifier si le clic est sur un port
        for port in self.ports.values():
            if port.contains(port.mapFromParent(event.pos())):
                # Le clic est sur un port, laisser le port le gérer
                return
        
        # Le clic est sur l'équipement lui-même
        print(f"Équipement cliqué: {self.equipment_id}")
        super().mousePressEvent(event)
    
    def get_port(self, port_id: str) -> Optional[PortGraphicsItem]:
        """Récupère un port par son ID"""
        return self.ports.get(port_id)
    
    def get_all_ports(self) -> List[PortGraphicsItem]:
        """Récupère tous les ports"""
        return list(self.ports.values())
    
    def connect_port(self, port_id: str):
        """Marque un port comme connecté"""
        port = self.get_port(port_id)
        if port:
            port.set_status(PortStatus.CONNECTED)
    
    def disconnect_port(self, port_id: str):
        """Marque un port comme déconnecté"""
        port = self.get_port(port_id)
        if port:
            port.set_status(PortStatus.DISCONNECTED)

# =============================================================================
# CLASSE FACTORY POUR CRÉER LES ÉQUIPEMENTS GRAPHIQUES
# =============================================================================

class EquipmentGraphicsFactory:
    """Factory pour créer les équipements graphiques selon leur type"""
    
    @staticmethod
    def create_equipment_graphics(equipment_id: str, equipment_def: dict, 
                                svg_path: str = None) -> EquipmentGraphicsItem:
        """Crée un équipement graphique selon sa définition"""
        
        return EquipmentGraphicsItem(equipment_id, equipment_def, svg_path)
