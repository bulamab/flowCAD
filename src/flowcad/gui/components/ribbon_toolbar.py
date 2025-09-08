"""
Barre d'outils style ribbon pour FlowCAD
"""
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QPushButton
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgRenderer

from pathlib import Path

class RibbonToolbar(QWidget):

    rotate_equipment = pyqtSignal(int)  # signal émis pour faire pivoter l'équipement sélectionné
    mirror_equipment = pyqtSignal(str)  # signal émis pour faire un miroir de l'équipement sélectionné
    align_equipment = pyqtSignal(str)  # signal émis pour aligner l'équipement sélectionné
    distribute_equipment = pyqtSignal(str)  # signal émis pour distribuer l'équipement sélectionné

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)  # Hauteur fixe pour le ribbon
        self.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc;")
        
        #le chemin vers les icones
        current_dir = Path(__file__).resolve().parent
        self.icon_path = current_dir.parents[1] / "resources" / "icons" / "toolbar"
        print(f"Chemin des icônes: {self.icon_path}")

        # Pour l'instant, juste un label
        self.setup_ui()
    
    def setup_ui(self):
    
        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(15)
        
        # === GROUPE TRANSFORMATION ===
        transform_group = self.create_tool_group(
            "Transformation",
            [
                {
                    'text': 'Rotate left',
                    'icon': 'rotate_left_90.svg',
                    'callback': self.on_rotate_90_left_clicked,
                    'tooltip': "Faire pivoter l'équipement sélectionné de 90° à gauche"
                },
                {
                    'text': 'Rotate right',
                    'icon': 'rotate_right_90.svg',
                    'callback': self.on_rotate_90_right_clicked,
                    'tooltip': "Faire pivoter l'équipement sélectionné de 90° à droite"
                },
                {
                    'text': 'Mirror H.',
                    'icon': 'Mirror_H.svg',
                    'callback': self.on_mirror_horizontal_clicked,
                    'tooltip': "Réfléchir l'équipement sélectionné autour de l'axe horizontal"
                },
                {
                    'text': 'Mirror V.',
                    'icon': 'Mirror_V.svg',
                    'callback': self.on_mirror_vertical_clicked,
                    'tooltip': "Réfléchir l'équipement sélectionné autour de l'axe vertical"
                },
                {
                    'text': 'Align V.',
                    'icon': 'Align_horizontal_center.svg',
                    'callback': self.on_align_horizontal_clicked,
                    'tooltip': "Aligner les équipements sélectionnés au centre horizontalement"
                },
                {
                    'text': 'Align H.',
                    'icon': 'Align_vertical_center.svg',
                    'callback': self.on_align_vertical_clicked,
                    'tooltip': "Aligner les équipements sélectionnés au centre verticalement"
                },
                {
                    'text': 'Distribute V.',
                    'icon': 'Distribute_vertical.svg',
                    'callback': self.on_distribute_vertical_clicked,
                    'tooltip': "Distribuer les équipements sélectionnés verticalement"
                },
                {
                    'text': 'Distribute H.',
                    'icon': 'Distribute_horizontal.svg',
                    'callback': self.on_distribute_horizontal_clicked,
                    'tooltip': "Distribuer les équipements sélectionnés horizontalement"
                }

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
                background-color: #f0f0f0;
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
        for tool in tools:
            tool_name = tool['text']
            icon = tool['icon']
            callback = tool['callback']
            tooltip = tool['tooltip']
            print(f"Création du bouton: {tool_name}", icon)
            button = self.create_tool_button(tool_name, icon, callback, tooltip)
            buttons_layout.addWidget(button)
        
        group_layout.addLayout(buttons_layout)
        
        return group_frame
    
    def create_tool_button(self, text: str, icon_name: str, callback, tooltip: str) -> QPushButton:
        """Crée un bouton d'outil standardisé"""
        
        button = QPushButton(text)
        button.setFixedSize(100, 45)  # Bouton carré
        button.setToolTip(tooltip)

        #charger l'icone
        svg_icon_path = self.icon_path / icon_name
        #créer un pixmap du SCG
        render = QSvgRenderer(str(svg_icon_path))
        pixmap = QPixmap(60, 45)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        render.render(painter)
        painter.end()
        button.setIcon(QIcon(pixmap))
        #button.setLayoutDirection(Qt.RightToLeft)

        # Style du bouton
        button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: #f0f0f0;
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

    def on_rotate_90_left_clicked(self):
        """Callback du bouton rotation"""
        print("🔄 Bouton rotation gauche cliqué")
        self.rotate_equipment.emit(-90)

    def on_rotate_90_right_clicked(self):
        """Callback du bouton rotation"""
        print("🔄 Bouton rotation cliqué")
        self.rotate_equipment.emit(90)

    def on_mirror_horizontal_clicked(self):
        """Callback du bouton miroir horizontal"""
        print("🔄 Bouton miroir horizontal cliqué")
        self.mirror_equipment.emit("h")
    
    def on_mirror_vertical_clicked(self):
        """Callback du bouton miroir vertical"""
        print("🔄 Bouton miroir vertical cliqué")
        self.mirror_equipment.emit("v")

    def on_align_vertical_clicked(self):
        """Callback du bouton alignement vertical"""
        print("🔄 Bouton alignement vertical cliqué")
        self.align_equipment.emit("v")

    def on_align_horizontal_clicked(self):
        """Callback du bouton alignement horizontal"""
        print("🔄 Bouton alignement horizontal cliqué")
        self.align_equipment.emit("h")  

    def on_distribute_vertical_clicked(self):
        """Callback du bouton distribution verticale"""
        print("🔄 Bouton distribution verticale cliqué")
        self.distribute_equipment.emit("v")

    def on_distribute_horizontal_clicked(self):
        """Callback du bouton distribution horizontale"""
        print("🔄 Bouton distribution horizontale cliqué")
        self.distribute_equipment.emit("h")

    def set_tool_enabled(self, tool_name: str, enabled: bool):
        """Active/désactive un outil (pour plus tard)"""
        # Pour l'instant, on peut désactiver manuellement
        # Plus tard, on pourra faire une recherche par nom
        pass
