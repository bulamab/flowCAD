# =============================================================================
# src/flowcad/gui/graphics/equipment_graphics.py
# =============================================================================
"""
Classes graphiques pour représenter les équipements hydrauliques sur le canvas
"""

from logging import root
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject, QByteArray, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen, QPainter, QTransform
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer 
import os
from enum import Enum
from typing import Dict, List, Optional

import re
import xml.etree.ElementTree as ET

from numpy import cos, sin, radians

from .pipe_style_manager import pipe_style_manager
from . svg_dynamic_manager import svg_dynamic_manager

#from .polyline_graphics import PolylineGraphicsItem

# =============================================================================
# ÉNUMÉRATION POUR L'ÉTAT DES PORTS
# =============================================================================

class PortVisualState(Enum):
    """États possibles d'un port hydraulique"""
    NORMAL = "normal"                # Apparence normale
    HIGHLIGHTED = "highlighted"      # Port en surbrillance (hover)
    SELECTED = "selected"           # Port sélectionné
    PREVIEW = "preview"           # Port en mode preview (ex: lors de la création de polyligne)

class PortConnectionStatus(Enum):
    """États possibles d'une connexion entre ports"""
    DISCONNECTED = "disconnected"    # Pas de connexion
    CONNECTED = "connected"          # Connexion établie
    PENDING = "pending"              # Connexion en attente
    RESERVED = "reserved"            # Connexion réservée

# =============================================================================
# CLASSE POUR UN PORT GRAPHIQUE
# =============================================================================

class PortGraphicsItem(QGraphicsEllipseItem):
    """Élément graphique représentant un port d'équipement"""
    
    # Couleurs selon l'état du port
    PORT_COLORS = {
        # Port libre
        (PortConnectionStatus.DISCONNECTED, PortVisualState.NORMAL): "#FF6B6B",         # Rouge : libre
        (PortConnectionStatus.DISCONNECTED, PortVisualState.HIGHLIGHTED): "#FFE066",    # Jaune : libre + hover
        (PortConnectionStatus.DISCONNECTED, PortVisualState.SELECTED): "#FF9FF3",       # Rose : libre + sélectionné
        (PortConnectionStatus.DISCONNECTED, PortVisualState.PREVIEW): "#95E1D3",        # Vert clair : libre + preview

        # Port connecté
        (PortConnectionStatus.CONNECTED, PortVisualState.NORMAL): "#4ECDC4",    # Vert : connecté
        (PortConnectionStatus.CONNECTED, PortVisualState.HIGHLIGHTED): "#A8E6CF", # Vert clair : connecté + hover
        (PortConnectionStatus.CONNECTED, PortVisualState.SELECTED): "#88D8C0",  # Vert foncé : connecté + sélectionné
        (PortConnectionStatus.CONNECTED, PortVisualState.PREVIEW): "#95E1D3",        # Vert clair : connecté + preview

        # Port réservé
        (PortConnectionStatus.RESERVED, PortVisualState.NORMAL): "#95A5A6",      # Gris : réservé
        (PortConnectionStatus.RESERVED, PortVisualState.HIGHLIGHTED): "#BDC3C7", # Gris clair : réservé + hover
        (PortConnectionStatus.RESERVED, PortVisualState.SELECTED): "#FF9FF3",       # Rose : réservé + sélectionné
        (PortConnectionStatus.RESERVED, PortVisualState.PREVIEW): "#95E1D3",        # Vert clair : réservé + preview

    }

    # Variable de contrôle pour l'affichage des ports connectés
    SHOW_CONNECTED_PORTS = False  # Par défaut, cacher les ports connectés
    
    def __init__(self, port_id: str, parent_equipment=None):
        # Cercle de rayon 12 pixels centré sur l'origine
        super().__init__(-6, -6, 12, 12)

        self.port_id = port_id
        self.parent_equipment = parent_equipment
        self.connection_status = PortConnectionStatus.DISCONNECTED  #etat logique du port
        self.visual_state = PortVisualState.NORMAL          #etat visuel du port

        self.force_visible = False  # Pour forcer l'affichage même si connecté

        self.setAcceptHoverEvents(True)
        
        # Rendre le port sélectionnable mais pas déplaçable individuellement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        #idée: les ports en z=2, les équipements en z=1, les polylignes en z=0
        self.setZValue(2)
        
        # Style initial
        self.update_appearance()
        #pour la visibilité du port
        self.update_visibility()
        
        # Tooltip informatif
        self.setToolTip(f"Port: {port_id}\nStatut: {self.connection_status.value}")

    def update_appearance(self):
        """Met à jour l'apparence selon l'état du port"""

        #couleur selon combinaison d'état visuel et de status
        color_key = (self.connection_status, self.visual_state)
        color = QColor(self.PORT_COLORS[color_key])

        # Couleur par défaut si combinaison non trouvée
        default_color = "#CCCCCC"
        color_hex = self.PORT_COLORS.get(color_key, default_color)
        color = QColor(color_hex)
        
        # Remplissage
        self.setBrush(QBrush(color))
        
        # Contour plus épais si sélectionné
        pen_width = 3 if self.visual_state == PortVisualState.SELECTED else 2
        self.setPen(QPen(Qt.black, pen_width))

    #méthodes pour gérer l'état logique (connecté/déconnecté)

    def update_tooltip(self):
        """Met à jour le tooltip avec les informations actuelles du port"""
        # Emoji selon le statut
        status_emoji = {
            PortConnectionStatus.DISCONNECTED: "🔴",
            PortConnectionStatus.CONNECTED: "🟢", 
            PortConnectionStatus.PENDING: "🟡",
            PortConnectionStatus.RESERVED: "🟠"
        }
        
        emoji = status_emoji.get(self.connection_status, "⚪")
        tooltip_text = f"{emoji} Port: {self.port_id}\nStatut: {self.connection_status.value}"
        
        # Ajouter des infos supplémentaires si connecté
        if self.connection_status == PortConnectionStatus.CONNECTED:
            tooltip_text += "\n💧 Connecté"
        elif self.connection_status == PortConnectionStatus.DISCONNECTED:
            tooltip_text += "\n🔓 Libre"
            
        # Ajouter info de visibilité si connecté
        if self.connection_status == PortConnectionStatus.CONNECTED:
            if not self.isVisible():
                tooltip_text += "\n👻 (Caché car connecté)"
            else:
                tooltip_text += "\n💧 Connecté"
        elif self.connection_status == PortConnectionStatus.DISCONNECTED:
            tooltip_text += "\n🔓 Libre"
            
        self.setToolTip(tooltip_text)

    def set_connection_status(self, status: PortConnectionStatus):
        """Change l'état du port"""
        print(f"Changement d'état du port {self.port_id} : {self.connection_status} -> {status}")
        if self.connection_status != status:
            self.connection_status = status
            self.update_appearance()    # Met à jour l'apparence du port
            self.update_tooltip()       # Met à jour le tooltip du port
            self.update_visibility()    # Met à jour la visibilité du port

    def is_free(self) -> bool:
        """vérifie si le port est libre"""
        return self.connection_status == PortConnectionStatus.DISCONNECTED

    def is_connected(self) -> bool:
        """vérifie si le port est connecté"""
        return self.connection_status == PortConnectionStatus.CONNECTED
    
    def can_connect(self) -> bool:
        """Vérifie si on peut connecter ce port"""
        return self.connection_status in [PortConnectionStatus.DISCONNECTED]

    #méthodes pour gérer l'état visuel----------------------------------

    # Met à jour la visibilité du port selon son statut de connexion
    def update_visibility(self):
        """Met à jour la visibilité du port selon son statut de connexion"""
        
        # Règles de visibilité :
        # 1. Si force_visible = True → toujours visible
        # 2. Si SHOW_CONNECTED_PORTS = True → toujours visible  
        # 3. Si port connecté et SHOW_CONNECTED_PORTS = False → invisible
        # 4. Sinon → visible
        
        should_be_visible = (
            self.force_visible or 
            PortGraphicsItem.SHOW_CONNECTED_PORTS or 
            self.connection_status != PortConnectionStatus.CONNECTED
        )
        
        if should_be_visible != self.isVisible():
            self.setVisible(should_be_visible)
            print(f"👻 Port {self.port_id} {'visible' if should_be_visible else 'invisible'}")

    def set_force_visible(self, visible: bool):
        """Force l'affichage du port (même si connecté)"""
        if self.force_visible != visible:
            self.force_visible = visible
            self.update_visibility()
            print(f"🔧 Port {self.port_id} force_visible = {visible}")

    def set_visual_state(self, state: PortVisualState):
        """Change l'état visuel du port"""
        if self.visual_state != state:
            self.visual_state = state
            self.update_appearance()
            self.update_tooltip()

    def highlight(self, enable=True):
        """Met en surbrillance ou retire la surbrillance"""
        if enable and self.visual_state == PortVisualState.NORMAL:
            self.set_visual_state(PortVisualState.HIGHLIGHTED)
        elif not enable and self.visual_state == PortVisualState.HIGHLIGHTED:
            self.set_visual_state(PortVisualState.NORMAL)

    def select(self, enable=True):
        """Sélectionne ou désélectionne visuellement"""
        if enable:
            self.set_visual_state(PortVisualState.SELECTED)
        else:
            # Retourner à l'état normal ou highlighted selon le contexte
            self.set_visual_state(PortVisualState.NORMAL)

    def mousePressEvent(self, event):
        
        """Gestion du clic sur le port"""
        if event.button() == Qt.LeftButton:
            
            # Récupérer le canvas parent
            canvas = None
            if self.scene() and hasattr(self.scene(), 'views'):
                views = self.scene().views()
                if views:
                    canvas = views[0]

            print(f"🔍 DEBUG: Clic sur port {self.port_id}")
            print(f"🔍 Canvas trouvé: {canvas is not None}")
            print(f"🔍 Mode interaction: {getattr(canvas, 'interaction_mode', 'NONE')}")
            
            # Vérifier le mode d'interaction
            print(f"Mode d'interaction: {canvas.interaction_mode}")
            if canvas and hasattr(canvas, 'interaction_mode'):
                if canvas.interaction_mode == "create_polyline":
                    # Mode création de polyligne
                    self.handle_polyline_click(canvas)
                    event.accept()
                    return

            print(f"Port cliqué: {self.port_id} de l'équipement {self.parent_equipment.equipment_id if self.parent_equipment else 'N/A'}")

            # Changer l'état pour montrer la sélection
            if self.visual_state != PortVisualState.SELECTED:
                self.set_visual_state(PortVisualState.SELECTED)
            else:
                self.set_visual_state(PortVisualState.NORMAL)

            # Empêcher la propagation à l'équipement parent
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Survol du port"""
        if self.visual_state == PortVisualState.NORMAL:
            self.set_visual_state(PortVisualState.HIGHLIGHTED)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol du port"""
        if self.visual_state == PortVisualState.HIGHLIGHTED:
            self.set_visual_state(PortVisualState.NORMAL)
        super().hoverLeaveEvent(event)

    def handle_polyline_click(self, canvas):
        """Gère les clics sur port en mode création de polyligne"""
        print(f"🔌 Clic sur port {self.port_id} en mode polyligne")
        
        # Vérifier si le port peut être connecté
        if not self.can_connect():
            print(f"❌ Port {self.port_id} ne peut pas être connecté (statut: {self.connection_status.value})")
            return
        
        # Appeler la méthode du canvas pour gérer la polyligne
        if hasattr(canvas, 'handle_port_click_for_polyline'):
            canvas.handle_port_click_for_polyline(self)

    # ✅ MÉTHODES DE CLASSE pour contrôler l'affichage global
    @classmethod
    def set_show_connected_ports(cls, show: bool):
        """Active/désactive l'affichage des ports connectés globalement"""
        if cls.SHOW_CONNECTED_PORTS != show:
            cls.SHOW_CONNECTED_PORTS = show
            print(f"🌍 Affichage global des ports connectés: {'ON' if show else 'OFF'}")
            
            # Notifier tous les ports existants de mettre à jour leur visibilité
            # (nécessite une référence aux ports existants)
            cls.update_all_ports_visibility()

    @classmethod  
    def update_all_ports_visibility(cls):
        """Met à jour la visibilité de tous les ports existants"""
        # Cette méthode sera appelée depuis le canvas qui a la liste des équipements
        print("🔄 Mise à jour de la visibilité de tous les ports...")

    @classmethod
    def get_show_connected_ports(cls):
        """Retourne l'état actuel de l'affichage des ports connectés"""
        return cls.SHOW_CONNECTED_PORTS

# =============================================================================
# CLASSE PRINCIPALE POUR UN ÉQUIPEMENT GRAPHIQUE
# =============================================================================

class EquipmentGraphicsItem(QGraphicsItem):
    """Élément graphique complet représentant un équipement hydraulique avec ses ports"""

    # L'échelle est définie globalement
    EQUIPEMENT_SCALE = 2

    # Variable de classe pour contrôler la migration
    USE_NEW_SVG_SYSTEM = True  # ✅ Toggle pour basculer facilement entre les systèmes (ancien et nouveau svg manager)

    def __init__(self, equipment_id: str, equipment_def: dict, svg_path: str = None, equipment_type: str = "generic"):
        super().__init__()
        
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type  # Type d'équipement (ex: pompe, réservoir, etc.)
        self.equipment_def = equipment_def
        self.svg_path = svg_path
        
        # Dimensions de base de l'équipement
        self.width = 60
        self.height = 60
        self.rotation_angle = 0  # Angle de rotation en degrés
        self.mirror_h = False
        self.mirror_v = False
        self.center = QPointF(30, 30)  # le centre, du SVG, pour les mirroirs et l'équilibre
        self.item_scale = EquipmentGraphicsItem.EQUIPEMENT_SCALE

        # État visuel actuel (pour les styles de tuyaux internes)
        self.current_visual_state = "normal"  # "normal", "selected", "hover"

        # Composants graphiques
        self.svg_item: Optional[QGraphicsSvgItem] = None # Élément SVG de l'équipement
        self.ports: Dict[str, PortGraphicsItem] = {}    # Ports de l'équipement
        self.ports_infos: List = [] # Informations sur les ports extraites du SVG
        
        # Rendre l'équipement déplaçable et sélectionnable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        #self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption, True)
        
        # Activer la détection de survol
        self.setAcceptHoverEvents(True)

        # Connecter aux changements de styles
        if self.USE_NEW_SVG_SYSTEM:
            svg_dynamic_manager.svg_modified.connect(self._on_svg_modified)
        else:
            # Ancien système
            pipe_style_manager.styles_changed.connect(self.on_pipe_styles_changed)

        # Stocker les propriétés de contenu SVG
        self.svg_content_properties = {}
        self._load_svg_content_properties()

        # Créer les composants
        self.create_components()
        self.create_ports()

        # Style de sélection personnalisé
        self.selection_pen = QPen(QColor(0, 120, 255), 2, Qt.DashLine)  # Bleu en pointillés
        self.selection_brush = QBrush(QColor(0, 120, 255, 30))  # Bleu transparent

        #liste des polylignes connectées
        self.connected_polylines: List = []  # Liste des polylignes à mettre à jour

    def create_components(self):
        """Crée les composants visuels de base"""
        
        # 1. Icône SVG ou fallback
        if self.svg_path and os.path.exists(self.svg_path):

            #extrait les informations du SVG
            self.ports_infos = self.read_ports_from_svg(self.svg_path)

            #creer le svg avec style
            self.create_styled_svg_item()

            #self.svg_item = QGraphicsSvgItem(self.svg_path)
            #self.svg_item.setParentItem(self)
            #print(f"dimensions: {self.svg_item.boundingRect().width()} x {self.svg_item.boundingRect().height()}")
            
            self.svg_item.setScale(self.item_scale)
            #redimensionner le bounding rect pour qu'il corresponde à la taille de l'élément SVG
            self.width = self.svg_item.boundingRect().width()*self.item_scale
            self.height = self.svg_item.boundingRect().height()*self.item_scale
            #fixer le centre du SVG
            

            self.center = self.svg_item.boundingRect().center()*self.item_scale
            #print(f"Centre avant: {self.center}")

    def create_styled_svg_item(self):
        """Crée l'item SVG avec les styles de tuyaux appliqués"""

        #print(f"scale {self.item_scale}")
        # Obtenir le SVG modifié avec les styles de tuyaux
        if self.USE_NEW_SVG_SYSTEM:
            styled_svg_content = self._create_svg_with_new_system()
        else:
            styled_svg_content = self._create_svg_with_old_system()

        #cacher les ports pour qu'ils ne soient pas visibles
        styled_svg_content=self.hide_svg_ports(styled_svg_content)

        
        if styled_svg_content:
            # Créer le renderer SVG à partir du contenu modifié
            svg_data = QByteArray(styled_svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_data)
            
            # Créer l'item SVG
            from PyQt5.QtSvg import QGraphicsSvgItem
            self.svg_item = QGraphicsSvgItem()
            self.svg_item.setSharedRenderer(renderer)
            self.svg_item.setParentItem(self)
            
            print(f"✅ SVG créé avec styles de tuyaux appliqués")
        else:
            # Fallback vers le SVG original
            self.svg_item = QGraphicsSvgItem(self.svg_path)
            self.svg_item.setParentItem(self)
            print(f"⚠️ Utilisation du SVG original (erreur de styling)")

    #Cache les ports svg. Des ports sont ajoutés sur Inkskape pour visualiser les connexions. IDéalement, ces ports ne 
    #sont pas visible sur le dessin, mais remplacés par les ports FlowCAD
    def hide_svg_ports(self, svg_content: str) -> str:
        """Cache les ports SVG"""

        # Parser le XML
        root = ET.fromstring(svg_content)
        
        # Masquer les ports
        for element in root.iter():
            element_id = element.get('id', '')
            
            if re.search(r'Port(\d+)', element_id, re.IGNORECASE):
                element.set('style', 'opacity:0')
                print(f"⚠️ Port masqué: {element_id}")

        svg_content = ET.tostring(root, encoding='unicode')
        return svg_content

    def update_visual_state(self, new_state: str):
        """Met à jour l'état visuel et les styles des tuyaux internes"""
        if self.current_visual_state != new_state:
            old_state = self.current_visual_state
            self.current_visual_state = new_state
            
            print(f"🎨 État visuel {self.equipment_id}: {old_state} → {new_state}")
            
            # Recréer le SVG avec les nouveaux styles
            self.update_svg_styles()

    def _load_svg_content_properties(self):
        """Charge les propriétés de contenu SVG depuis equipment_def"""
        svg_dynamic = self.equipment_def.get('svg_dynamic', {})
        content_config = svg_dynamic.get('content', {})
        text_elements = content_config.get('text_elements', {})
        
        for element_id, config in text_elements.items():
            property_link = config.get('property_link')
            if property_link:
                # Récupérer la valeur initiale depuis properties
                initial_value = self.equipment_def.get('properties', {}).get(
                    property_link,
                    config.get('default', '')
                )
                self.svg_content_properties[element_id] = {
                    'property_link': property_link,
                    'value': initial_value
                }
                print(f"📋 Propriété SVG chargée: {element_id} → {property_link} = '{initial_value}'")

    def _create_svg_with_new_system(self) -> Optional[str]:
        """✅ Crée le SVG avec le nouveau système (SVGDynamicManager)"""
        
        modifications = {
            'styles': {
                'pipe_state': self.current_visual_state,
                'scale_factor': self.item_scale
            }
        }

        #  Ajouter les modifications de contenu
        if self.svg_content_properties:
            text_mods = {}
            for element_id, config in self.svg_content_properties.items():
                text_mods[element_id] = str(config['value'])
            
            modifications['content'] = {
                'text_elements': text_mods
            }
            print(f"📝 Modifications de contenu: {text_mods}")

        
        return svg_dynamic_manager.modify_svg(
            self.svg_path,
            self.equipment_id,
            modifications
        )
    
    def _create_svg_with_old_system(self) -> Optional[str]:
        """⚠️ Crée le SVG avec l'ancien système (pipe_style_manager)"""
        
        styled_svg_content = pipe_style_manager.apply_pipe_styles_to_svg(
            self.svg_path,
            self.current_visual_state,
            self.item_scale
        )
        
        return styled_svg_content

    def update_svg_styles(self):
        """Met à jour les styles du SVG selon l'état actuel"""
        if not self.svg_path or not self.svg_item:
            return
        
        if self.USE_NEW_SVG_SYSTEM:
            # ✅ NOUVEAU SYSTÈME
            self._update_svg_with_new_system()
        else:
            # ⚠️ ANCIEN SYSTÈME
            self._update_svg_with_old_system()
    
    def _update_svg_with_new_system(self):
        """✅ Met à jour avec le nouveau système"""
        
        modifications = {
            'styles': {
                'pipe_state': self.current_visual_state,
                'scale_factor': self.item_scale
            }
        }
        
        #  Ajouter les modifications de contenu
        if self.svg_content_properties:
            text_mods = {}
            for element_id, config in self.svg_content_properties.items():
                text_mods[element_id] = str(config['value'])
            
            modifications['content'] = {
                'text_elements': text_mods
            }


        styled_svg_content = svg_dynamic_manager.modify_svg(
            self.svg_path,
            self.equipment_id,
            modifications
        )
        
        if styled_svg_content:
            # Cacher les ports
            styled_svg_content = self.hide_svg_ports(styled_svg_content)
            
            # Mettre à jour le renderer
            svg_data = QByteArray(styled_svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_data)
            self.svg_item.setSharedRenderer(renderer)
            
            print(f"🔄 Styles SVG mis à jour pour {self.equipment_id} (nouveau système)")
    
    def set_svg_text_property(self, element_id: str, new_value: str):
        """
        Définit la valeur d'une propriété texte SVG
        
        Args:
            element_id: ID de l'élément SVG (ex: 'Name')
            new_value: Nouvelle valeur du texte
        """
        if element_id in self.svg_content_properties:
            old_value = self.svg_content_properties[element_id]['value']
            self.svg_content_properties[element_id]['value'] = new_value
            
            # Mettre à jour aussi dans equipment_def.properties
            property_link = self.svg_content_properties[element_id]['property_link']
            if 'properties' not in self.equipment_def:
                self.equipment_def['properties'] = {}
            self.equipment_def['properties'][property_link] = new_value
            
            print(f"✏️ Propriété SVG modifiée: {element_id} '{old_value}' → '{new_value}'")
            
            # Rafraîchir le SVG
            self.update_svg_styles()
        else:
            print(f"⚠️ Propriété SVG '{element_id}' non trouvée")

    def _update_svg_with_old_system(self):
        """⚠️ Met à jour avec l'ancien système"""
        
        styled_svg_content = pipe_style_manager.apply_pipe_styles_to_svg(
            self.svg_path,
            self.current_visual_state,
            self.item_scale
        )
        
        # Cacher les ports
        styled_svg_content = self.hide_svg_ports(styled_svg_content)
        
        if styled_svg_content:
            svg_data = QByteArray(styled_svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_data)
            self.svg_item.setSharedRenderer(renderer)
            
            print(f"🔄 Styles SVG mis à jour pour {self.equipment_id} (ancien système)")
    
    def _on_svg_modified(self, equipment_id: str, svg_content: str):
        """Callback quand un SVG est modifié (nouveau système)"""
        if equipment_id == self.equipment_id:
            print(f"📡 Signal reçu: SVG modifié pour {equipment_id}")
            # Le SVG a déjà été mis à jour par modify_svg
    
    def __del__(self):
        """Nettoyage lors de la destruction"""
        try:
            if self.USE_NEW_SVG_SYSTEM:
                svg_dynamic_manager.svg_modified.disconnect(self._on_svg_modified)
            else:
                pipe_style_manager.styles_changed.disconnect(self.on_pipe_styles_changed)
        except:
            pass

    def on_pipe_styles_changed(self):
        """Callback quand les styles globaux des tuyaux changent"""
        print(f"🎨 Styles globaux changés - mise à jour {self.equipment_id}")
        self.update_svg_styles()
    
    def set_item_scale(self, new_scale: float):
        """
        Modifie l'échelle de l'équipement et met à jour les styles en conséquence
        
        Args:
            new_scale: Nouveau facteur d'échelle
        """
        if abs(self.item_scale - new_scale) > 0.001:  # Éviter les mises à jour inutiles
            old_scale = self.item_scale
            self.item_scale = new_scale
            
            # Appliquer l'échelle au SVG
            if self.svg_item:
                self.svg_item.setScale(new_scale)
            
            # Recalculer les dimensions
            if self.svg_item:
                self.width = self.svg_item.boundingRect().width() * self.item_scale
                self.height = self.svg_item.boundingRect().height() * self.item_scale
            
            # Mettre à jour les styles avec la nouvelle échelle
            self.update_svg_styles()
            
            print(f"📏 Échelle {self.equipment_id}: {old_scale:.3f} → {new_scale:.3f}")
    
    def get_effective_stroke_width(self, base_width: float) -> float:
        """Retourne l'épaisseur effective d'un trait selon l'échelle actuelle"""
        return pipe_style_manager.calculate_optimal_stroke_width(base_width, self.item_scale)

    def get_scale_info(self) -> dict:
        """Retourne des informations sur l'échelle et les ajustements"""
        base_style = pipe_style_manager.get_pipe_style(self.current_visual_state)
        scaled_style = pipe_style_manager.get_scaled_pipe_style(self.current_visual_state, self.item_scale)
        
        return {
            'item_scale': self.item_scale,
            'visual_state': self.current_visual_state,
            'base_stroke_width': base_style.get('stroke-width', 'N/A'),
            'scaled_stroke_width': scaled_style.get('stroke-width', 'N/A'),
            'svg_dimensions': f"{self.width:.1f}x{self.height:.1f}"
        }

    def __del__(self):
        """Nettoyage lors de la destruction"""
        # Se déconnecter des signaux pour éviter les fuites mémoire
        try:
            pipe_style_manager.styles_changed.disconnect(self.on_pipe_styles_changed)
        except:
            pass

    #Lit le nombre de ports et leur position en fonction des informations contenues dans le SVG----------------
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
        print(f"\nElement default size: {self.width} x {self.height}")

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

    #créé les ports à partir de la liste des ports extraite du SVG
    def create_ports(self):
        """Crée les ports selon les valeurs lues dans le SVG"""
        for port_info in self.ports_infos:
            x = port_info['x']*self.item_scale
            y = port_info['y']*self.item_scale
            self.create_port(f"P{port_info['port']}", x, y)

    # Crée un port individuel, à partir des coordronnées
    def create_port(self, port_id: str, x: float, y: float):
        """Crée un port individuel"""

        port_item = PortGraphicsItem(port_id, parent_equipment=self)
        port_item.setParentItem(self)

        port_item.setPos(x, y)
        
        # Stocker le port
        self.ports[port_id] = port_item

    #bounding rectangle (classe abstraite de QGraphicsItem)
    #définit la zone de collision/sélection complète
    def boundingRect(self) -> QRectF:
        """Définit la zone de collision/sélection complète"""
        
        # Zone principale de l'équipement
        margin = 0 #une marge pour "englober les ports. Le but est que l'élément reste symétrique"
        equipment_rect = QRectF(0-margin, 0-margin, self.width+margin, self.height+margin)
        #print(f"boundingRect: {equipment_rect.width()} x {equipment_rect.height()}")

        # Inclure les ports (avec une marge pour faciliter la sélection)
        #port_margin = 3
        for port in self.ports.values():
            port_rect = port.boundingRect()
            port_rect.translate(port.pos())
            #port_rect.adjust(-port_margin, -port_margin, port_margin, port_margin)
            equipment_rect = equipment_rect.united(port_rect)
        
        #print(f"boundingRect final: {equipment_rect.width()} x {equipment_rect.height()}")
        return equipment_rect
    
    #dessin de l'équipement (classe abstraite de QGraphicsItem)
    # définit la méthode de dessin
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

        #Si l'élément est séectionné, dessiner la boîte de sélection
        if self.isSelected():
            self.draw_selection_box(painter)

    # Dessine la boîte de sélection visible
    def draw_selection_box(self, painter: QPainter):
        """Dessine la boîte de sélection visible"""
        
        # Récupérer le rectangle de sélection
        bounding_rect = self.boundingRect()
        
        # Ajouter une petite marge pour que ce soit plus visible
        margin = 3
        selection_rect = bounding_rect.adjusted(-margin, -margin, margin, margin)
        
        # Dessiner le fond transparent
        painter.setBrush(self.selection_brush)
        painter.setPen(self.selection_pen)
        painter.drawRect(selection_rect)
        
        # ✅ OPTION : Dessiner des "poignées" de redimensionnement aux coins
        self.draw_selection_handles(painter, selection_rect)

    #Dessine des petites poignées aux coins (optionnel)
    def draw_selection_handles(self, painter: QPainter, rect: QRectF):
        """Dessine des petites poignées aux coins (optionnel)"""
        
        handle_size = 6
        handle_pen = QPen(QColor(0, 120, 255), 1)
        handle_brush = QBrush(Qt.white)
        
        painter.setPen(handle_pen)
        painter.setBrush(handle_brush)
        
        # Positions des poignées (coins + milieux)
        handles = [
            # Coins
            (rect.topLeft(), "top-left"),
            (rect.topRight(), "top-right"), 
            (rect.bottomLeft(), "bottom-left"),
            (rect.bottomRight(), "bottom-right"),
            # Milieux (optionnel)
            (rect.center().x(), rect.top()),      # Haut
            (rect.center().x(), rect.bottom()),   # Bas
            (rect.left(), rect.center().y()),     # Gauche
            (rect.right(), rect.center().y())     # Droite
        ]
        
        for handle in handles[:4]:  # Seulement les coins pour l'instant
            if isinstance(handle[0], tuple):
                x, y = handle[0]
            else:
                x, y = handle[0].x(), handle[0].y()
            
            handle_rect = QRectF(x - handle_size/2, y - handle_size/2, handle_size, handle_size)
            painter.drawRect(handle_rect)
    
    def mousePressEvent(self, event):
        """Gestion des clics sur l'équipement"""
        
        """# Vérifier si le clic est sur un port
        for port in self.ports.values():
            if port.contains(port.mapFromParent(event.pos())):
                # Le clic est sur un port, laisser le port le gérer
                port.mousePressEvent(event)
                return"""
        
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
            port.set_connection_status(PortConnectionStatus.CONNECTED)
    
    def disconnect_port(self, port_id: str):
        """Marque un port comme déconnecté"""
        port = self.get_port(port_id)
        if port:
            port.set_connection_status(PortConnectionStatus.DISCONNECTED)

    def get_free_ports(self) -> List[PortGraphicsItem]:
        """Récupère tous les ports libres"""
        return [port for port in self.ports.values() if port.is_free()]

    def get_connected_ports(self) -> List[PortGraphicsItem]:
        """Récupère tous les ports connectés"""
        return [port for port in self.ports.values() if port.is_connected()]

    def itemChange(self, change, value):
        """Réagit aux changements d'état de l'item"""

        if self.scene():
            old_scene_rect = self.mapRectToScene(self.boundingRect())
            old_scene_rect = old_scene_rect.adjusted(-10, -10, 10, 10)  # Marge de sécurité
            self.scene().update(old_scene_rect)
        
        if change == QGraphicsItem.ItemSelectedChange:
            # L'état de sélection a changé
            new_visual_state = "selected" if value else "normal"
            self.update_visual_state(new_visual_state)

            if value:
                print(f"✅ Équipement sélectionné: {self.equipment_id}")
        
            else:
                print(f"❌ Équipement désélectionné: {self.equipment_id}")

        elif change == QGraphicsItem.ItemPositionHasChanged:
            #si l'objet est bougé, mettre à jour la polyligne
            self.update_connected_polylines()
            if self.scene():
                new_scene_rect = self.mapRectToScene(self.boundingRect())
                new_scene_rect = new_scene_rect.adjusted(-10, -10, 10, 10)  # Marge de sécurité
                self.scene().update(new_scene_rect)

        return super().itemChange(change, value)
    
    #fonction qui tourne l'équipement d'un angle donné
    def set_rotation_angle(self, angle: float):
        """Fait pivoter l'équipement d'un certain angle (en degrés)"""
        self.rotation_angle = (self.rotation_angle + angle) % 360
        self.update_transform()

    #fonction qui fait un mirroir selon l'axe vertical
    def set_mirror_direction(self, direction: str):
        """Fait un mirroir de l'équipement selon la direction spécifiée"""

        if direction == "h":
            self.mirror_h = not self.mirror_h  # toggle horizontal
        elif direction == "v":
            self.mirror_v = not self.mirror_v  # toggle vertical
        self.update_transform()

    def update_transform(self):
        t = QTransform()
        #enter = self.boundingRect().center()
        enter = self.center
        print(f"Centre de l'équipement: {enter.x()}, {enter.y()}")
        #transformations de l'equipement
        print(f"Transformations: rotation {self.rotation_angle}°, miroir_h {self.mirror_h}, miroir_v {self.mirror_v}")
        # 1. Translation au centre
        t.translate(enter.x(), enter.y())
        # 2. Appliquer le miroir (scale)
        if self.rotation_angle in [90, 270]:
            #si l'angle est à 90 ou 270, inverser les axes de miroir
            sx = -1 if self.mirror_h else 1
            sy = -1 if self.mirror_v else 1
        else:
            sx = -1 if self.mirror_v else 1
            sy = -1 if self.mirror_h else 1
        t.scale(sx, sy)
        # 3. Appliquer la rotation (autour du centre)
        #changer le sens de rotation si un mirroir a été fait
        if self.mirror_h ^ self.mirror_v:
            t.rotate(-self.rotation_angle)
        else:
            t.rotate(self.rotation_angle)
        # 4. Revenir au centre d'origine
        t.translate(-enter.x(), -enter.y())
        self.setTransform(t)
        self.update()

    def add_connected_polyline(self, polyline):
        """Ajoute une polyligne à la liste des connexions de cet équipement"""
        if polyline not in self.connected_polylines:
            self.connected_polylines.append(polyline)
            print(f"🔗 Polyligne ajoutée aux connexions de {self.equipment_id}")
    
    def remove_connected_polyline(self, polyline):
        """Retire une polyligne de la liste des connexions"""
        if polyline in self.connected_polylines:
            self.connected_polylines.remove(polyline)
            print(f"🔗 Polyligne retirée des connexions de {self.equipment_id}")
    
    def update_connected_polylines(self):
        """Met à jour toutes les polylignes connectées à cet équipement"""
        for polyline in self.connected_polylines:
            if hasattr(polyline, 'update_connection_points'):
                polyline.update_connection_points()
            else:
                print(f"⚠️ Polyligne sans méthode update_connection_points")

        print(f"🔄 {len(self.connected_polylines)} polylignes mises à jour pour {self.equipment_id}")

    def update_properties(self, new_def: dict):
        """Met à jour les propriétés de l'équipement"""
        # Effacer les résultats avant de mettre à jour les propriétés
        self.clear_results()

        #seules les propriétés editables sont mises à jour
        self.equipment_def['properties'].update(new_def)
        print(f"🔧 Propriétés mises à jour pour {self.equipment_id}: {new_def}")

    # Dans src/flowcad/gui/graphics/equipment_graphics.py
    def clear_results(self):
        """Efface tous les résultats de l'équipement"""
        if 'results' in self.equipment_def:
            # Réinitialiser tous les résultats à 0.0
            for key in self.equipment_def['results'].keys():
                self.equipment_def['results'][key] = 0.0
            print(f"🧹 Résultats effacés pour {self.equipment_id}")




# =============================================================================
# CLASSE FACTORY POUR CRÉER LES ÉQUIPEMENTS GRAPHIQUES
# =============================================================================

class EquipmentGraphicsFactory:
    """Factory pour créer les équipements graphiques selon leur type"""
    
    @staticmethod
    def create_equipment_graphics(equipment_id: str, equipment_def: dict,
                                svg_path: str = None, equipment_type: str = "generic") -> EquipmentGraphicsItem:
        """Crée un équipement graphique selon sa définition"""

        return EquipmentGraphicsItem(equipment_id, equipment_def, svg_path, equipment_type)
