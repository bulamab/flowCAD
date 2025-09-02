# =============================================================================
# src/flowcad/gui/graphics/equipment_graphics.py
# =============================================================================
"""
Classes graphiques pour représenter les équipements hydrauliques sur le canvas
"""

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QBrush, QPen, QPainter
from PyQt5.QtSvg import QGraphicsSvgItem
import os
from enum import Enum
from typing import Dict, List, Optional

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

class PortType(Enum):
    """Types de ports hydrauliques"""
    HYDRAULIC_INLET = "hydraulic_inlet"      # Entrée hydraulique
    HYDRAULIC_OUTLET = "hydraulic_outlet"    # Sortie hydraulique
    CONTROL_SIGNAL = "control_signal"        # Signal de contrôle
    POWER = "power"                         # Alimentation électrique

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
    
    def __init__(self, port_id: str, port_type: PortType, parent_equipment=None):
        # Cercle de rayon 8 pixels centré sur l'origine
        super().__init__(-8, -8, 16, 16)
        
        self.port_id = port_id
        self.port_type = port_type
        self.parent_equipment = parent_equipment
        self.status = PortStatus.DISCONNECTED
        
        # Rendre le port sélectionnable mais pas déplaçable individuellement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Style initial
        self.update_appearance()
        
        # Tooltip informatif
        self.setToolTip(f"Port: {port_id}\nType: {port_type.value}")
    
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
            print(f"Port cliqué: {self.port_id} (Type: {self.port_type.value})")
            
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
        
        # Composants graphiques
        self.svg_item: Optional[QGraphicsSvgItem] = None
        self.text_item: Optional[QGraphicsTextItem] = None
        self.ports: Dict[str, PortGraphicsItem] = {}
        
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
            self.svg_item = QGraphicsSvgItem(self.svg_path)
            self.svg_item.setParentItem(self)
            # Redimensionner le SVG
            self.svg_item.setScale(min(self.width / self.svg_item.boundingRect().width(),
                                     self.height / self.svg_item.boundingRect().height()))
        
        # 2. Nom de l'équipement
        display_name = self.equipment_def.get('display_name', self.equipment_id)
        self.text_item = QGraphicsTextItem(display_name)
        self.text_item.setParentItem(self)
        
        # Positionner le texte sous l'équipement
        text_rect = self.text_item.boundingRect()
        text_x = (self.width - text_rect.width()) / 2
        text_y = self.height + 5
        self.text_item.setPos(text_x, text_y)
    
    def create_ports(self):
        """Crée les ports selon la définition de l'équipement"""
        
        # Récupérer les définitions de ports depuis equipment_def
        # (À adapter selon votre structure JSON)
        ports_config = self.equipment_def.get('ports', {})
        
        if not ports_config:
            # Configuration par défaut si pas de ports définis
            ports_config = self.get_default_ports_config()
        
        for port_id, port_config in ports_config.items():
            self.create_port(port_id, port_config)
    
    def get_default_ports_config(self) -> dict:
        """Configuration par défaut des ports selon le type d'équipement"""
        
        # Règles par défaut basées sur le nom de l'équipement
        equipment_name = self.equipment_def.get('display_name', '').lower()
        
        if 'pompe' in equipment_name:
            return {
                'inlet': {'type': PortType.HYDRAULIC_INLET, 'position': 'left'},
                'outlet': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'}
            }
        elif 'vanne' in equipment_name:
            return {
                'inlet': {'type': PortType.HYDRAULIC_INLET, 'position': 'left'},
                'outlet': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'}
            }
        elif 'pression' in equipment_name or 'débit' in equipment_name:
            return {
                'outlet': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'}
            }
        else:
            # Défaut générique
            return {
                'port1': {'type': PortType.HYDRAULIC_INLET, 'position': 'left'},
                'port2': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'}
            }
    
    def create_port(self, port_id: str, port_config: dict):
        """Crée un port individuel"""
        
        # Type de port
        port_type_str = port_config.get('type', PortType.HYDRAULIC_INLET)
        if isinstance(port_type_str, str):
            port_type = PortType(port_type_str)
        else:
            port_type = port_type_str
        
        # Créer le port graphique
        port_item = PortGraphicsItem(port_id, port_type, parent_equipment=self)
        port_item.setParentItem(self)
        
        # Positionner le port
        port_position = port_config.get('position', 'left')
        self.position_port(port_item, port_position)
        
        # Stocker le port
        self.ports[port_id] = port_item
    
    def position_port(self, port_item: PortGraphicsItem, position: str):
        """Positionne un port selon sa configuration"""
        
        margin = 8  # Distance du bord de l'équipement
        
        if position == 'left':
            port_item.setPos(-margin, self.height / 2)
        elif position == 'right':
            port_item.setPos(self.width + margin, self.height / 2)
        elif position == 'top':
            port_item.setPos(self.width / 2, -margin)
        elif position == 'bottom':
            port_item.setPos(self.width / 2, self.height + margin)
        else:
            # Position par défaut
            port_item.setPos(0, self.height / 2)
    
    def boundingRect(self) -> QRectF:
        """Définit la zone de collision/sélection complète"""
        
        # Zone principale de l'équipement
        equipment_rect = QRectF(0, 0, self.width, self.height)
        
        # Inclure le texte
        if self.text_item:
            text_rect = self.text_item.boundingRect()
            text_rect.translate(self.text_item.pos())
            equipment_rect = equipment_rect.united(text_rect)
        
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

# =============================================================================
# STRUCTURE DE FICHIERS RECOMMANDÉE
# =============================================================================

"""
Structure recommandée :

src/flowcad/gui/
├── graphics/
│   ├── __init__.py
│   ├── equipment_graphics.py      # Ce fichier
│   ├── connection_graphics.py     # Pour les tuyaux (plus tard)
│   └── port_graphics.py          # Si les ports deviennent complexes
├── components/
│   ├── equipment_panel.py         # Panneau de sélection
│   ├── drawing_canvas.py          # Zone de dessin
│   └── properties_panel.py        # Panneau des propriétés
└── main_window.py
"""

# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

def test_equipment_graphics():
    """Test des équipements graphiques avec ports"""
    import sys
    from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # Créer une scène de test
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setSceneRect(0, 0, 800, 600)
    
    # Définitions d'équipements de test
    pump_def = {
        'display_name': 'Pompe Test',
        'color': '#FF6B6B',
        'ports': {
            'inlet': {'type': PortType.HYDRAULIC_INLET, 'position': 'left'},
            'outlet': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'}
        }
    }
    
    valve_def = {
        'display_name': 'Vanne Test',
        'color': '#4ECDC4',
        'ports': {
            'inlet': {'type': PortType.HYDRAULIC_INLET, 'position': 'left'},
            'outlet': {'type': PortType.HYDRAULIC_OUTLET, 'position': 'right'},
            'control': {'type': PortType.CONTROL_SIGNAL, 'position': 'top'}
        }
    }
    
    # Créer des équipements
    pump = EquipmentGraphicsItem('PUMP_001', pump_def)
    pump.setPos(100, 100)
    scene.addItem(pump)
    
    valve = EquipmentGraphicsItem('VALVE_001', valve_def)
    valve.setPos(300, 100)
    scene.addItem(valve)
    
    # Afficher
    view.show()
    view.setWindowTitle("Test Équipements avec Ports")
    
    print("Instructions:")
    print("- Cliquez sur les cercles colorés (ports) pour les sélectionner")
    print("- Cliquez sur les équipements pour les déplacer") 
    print("- Les ports changent de couleur selon leur état")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_equipment_graphics()