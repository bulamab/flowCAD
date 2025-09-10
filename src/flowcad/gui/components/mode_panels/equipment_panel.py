"""
Panneau des équipements - Lit la config depuis JSON
"""
import os
import json

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                            QLabel, QScrollArea, QGridLayout, QFrame, QGraphicsView,
                            QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QByteArray, QDataStream, QIODevice
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QDrag, QPainter, QPixmap, QBrush, QPen, QColor

from typing import List, Dict, Any
from pathlib import Path


from ....config.equipment.equipment_loader import EquipmentLoader

class DraggableEquipmentWidget(QFrame):
    """Widget d'équipement qui peut être dragué"""
    
    def __init__(self, equipment_id: str, equipment_def: dict, equipment_properties: dict, parent=None):
        super().__init__(parent)
        self.equipment_id = equipment_id
        self.equipment_def = equipment_def
        self.equipment_properties = equipment_properties
        self.equipment_loader = EquipmentLoader()
        
        self.setFixedSize(80, 90)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #FFFFFF;
            }
            QFrame:hover {
                background-color: #FFFFFF;
                border: 2px solid #4CAF50;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface du widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        svg_path = self.equipment_loader.get_svg_path(self.equipment_id)
        svg_widget = self.create_svg_widget(svg_path, self.equipment_def.get('color', '#666'))
        layout.addWidget(svg_widget, alignment=Qt.AlignCenter)

        ## Placeholder coloré (en attendant les vrais SVG)
        #color = self.equipment_def.get('color', '#666')
        #icon_widget = QWidget()
        #icon_widget.setFixedSize(50, 35)
        #icon_widget.setStyleSheet(f"""
        #    background-color: {color};
        #    border: 1px solid #999;
        #    border-radius: 3px;
        #""")
        #layout.addWidget(icon_widget, alignment=Qt.AlignCenter)
        
        # Nom de l'équipement
        name_label = QLabel(self.equipment_def.get('display_name', self.equipment_id))
        name_label.setFixedHeight(22)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 10px; color: #333; border: none;")
        layout.addWidget(name_label)

        
    
    def mousePressEvent(self, event):
        """Début du drag & drop"""
        if event.button() == Qt.LeftButton:
            print(f"Début du drag pour: {self.equipment_id}")
            
            # Créer les données à transférer
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Encoder les données de l'équipement en JSON
            equipment_data = {
                'equipment_id': self.equipment_id,
                'equipment_def': self.equipment_def,
                'type': 'flowcad_equipment'
            }
            
            json_data = json.dumps(equipment_data)
            mime_data.setData('application/x-flowcad-equipment', QByteArray(json_data.encode()))
            
            drag.setMimeData(mime_data)
            
            # Créer une image de drag (miniature)
            drag_pixmap = self.create_drag_pixmap()
            drag.setPixmap(drag_pixmap)
            drag.setHotSpot(drag_pixmap.rect().center())
            
            # Exécuter le drag
            drag.exec_(Qt.CopyAction)
    
    def create_drag_pixmap(self) -> QPixmap:
        """Crée l'image affichée pendant le drag"""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)  # Légèrement transparent
        self.render(painter)
        painter.end()
        
        return pixmap
    
    def create_svg_widget(self, svg_path: str, color: str):
        """Crée un widget SVG ou un placeholder coloré"""
        
        # Vérifier si le fichier SVG existe
        path = Path(svg_path)
        print( f"Chemin SVG: {path}, Exists: {path.exists()}" )
        if path.exists():
            # Afficher le vrai SVG
            svg_widget = QSvgWidget(str(path))
            svg_widget.setFixedSize(60, 60)
            svg_widget.setStyleSheet("border: none;")
            return svg_widget
        else:
            # Placeholder coloré si pas de SVG
            placeholder = QWidget()
            placeholder.setFixedSize(50, 35)
            placeholder.setStyleSheet(f"""
                background-color: {color};
                border: none;
            """)
            return placeholder


class EquipmentPanel(QWidget):
    # Signal émis quand un équipement est sélectionné
    equipment_selected = pyqtSignal(str, str)  # (category, equipment_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #e8e8e8; border-right: 1px solid #ccc;")
        
        # Créer le loader
        self.equipment_loader = EquipmentLoader()
        
        self.setup_ui()
        self.populate_tree_from_config()
    
    def setup_ui(self):
        """Configure l'interface du panneau"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        """# Titre
        title = QLabel("🔧 Équipements")
        title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")
        layout.addWidget(title)"""
        
        # Arbre des catégories
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Équipements")
        #self.tree.setHeaderHidden(True)
        self.tree.setMaximumHeight(200)
        self.tree.itemClicked.connect(self.on_tree_clicked)
        layout.addWidget(self.tree)

        #POur le header, le style
        self.tree.setStyleSheet("""
            QHeaderView::section {
            background-color: #e8e8e8;   /* Fond gris clair */
            color: black;                /* Texte noir */
            font-weight: bold;           /* Gras */
            border: 1px solid #1B4F72;   /* Bordure */
            padding: 4px;
        }
        """)
        
        # Zone pour les icônes (pour plus tard)
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        self.icons_widget = QWidget()
        self.icons_layout = QGridLayout(self.icons_widget)
        
        scroll_area.setWidget(self.icons_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def populate_tree_from_config(self):
        """Remplit l'arbre depuis le fichier de configuration"""
        categories = self.equipment_loader.get_categories()
        
        # Nettoyer l'arbre
        self.tree.clear()
        
        # Construire l'arbre récursivement
        for category_id, category_data in categories.items():
            self.add_category_to_tree(None, category_id, category_data)
        
        # Développer tous les nœuds
        #self.tree.expandAll()
    
    def add_category_to_tree(self, parent_item, category_id, category_data):
        """Ajoute une catégorie (et ses sous-catégories) à l'arbre"""
        
        # Nom à afficher
        display_name = category_data.get('display_name', category_id)
        
        # Créer l'élément de l'arbre
        if parent_item is None:
            # Élément racine
            tree_item = QTreeWidgetItem(self.tree, [display_name])
        else:
            # Sous-élément
            tree_item = QTreeWidgetItem(parent_item, [display_name])
        
        # Stocker l'ID de la catégorie dans l'élément
        tree_item.setData(0, Qt.UserRole, category_id)

        # Stocker aussi les équipements de cette catégorie
        equipment_items = category_data.get('equipment_items', [])
        tree_item.setData(1, Qt.UserRole, equipment_items)

        
        # Traiter les sous-catégories s'il y en a
        subcategories = category_data.get('subcategories', {})
        for sub_id, sub_data in subcategories.items():
            self.add_category_to_tree(tree_item, sub_id, sub_data)
    
    def on_tree_clicked(self, item, column):
        """Callback quand on clique sur un élément de l'arbre"""
        
        category_id = item.data(0, Qt.UserRole)
        display_name = item.text(0)
        equipment_items = item.data(1, Qt.UserRole) or []
        
        print(f"Catégorie cliquée: {display_name} (ID: {category_id})")
        print(f"Équipements: {equipment_items}")
        
        # Effacer la zone d'icônes
        self.clear_icons()
        
        # Afficher les équipements de cette catégorie
        if equipment_items:
            self.display_draggable_equipment(equipment_items)

    def clear_icons(self):
        """Efface la zone d'icônes"""
        for i in reversed(range(self.icons_layout.count())):
            child = self.icons_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

    def display_draggable_equipment(self, equipment_list: List[str]):
        """Affiche les icônes SVG des équipements"""
        row, col = 0, 0
        max_cols = 2  # 2 colonnes

        for equipment_id in equipment_list:
            # Récupérer les infos de l'équipement
            equipment_def = self.equipment_loader.get_single_equipment_definition(equipment_id)
            equipment_properties = self.equipment_loader.get_single_equipment_properties(equipment_id)

            if equipment_def:
                # Créer le widget pour cet équipement
                draggable_widget = DraggableEquipmentWidget(equipment_id, equipment_def, equipment_properties)
                self.icons_layout.addWidget(draggable_widget, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
    
    def on_equipment_clicked(self, equipment_id: str, equipment_def: Dict[str, Any], equipment_properties: Dict[str, Any]):
        """Callback quand un équipement est cliqué"""
        
        display_name = equipment_def.get('display_name', equipment_id)
        print(f"Équipement cliqué: {equipment_id} -> {display_name}")
        
        # Émettre le signal
        self.equipment_selected.emit(equipment_id, display_name, equipment_properties)


