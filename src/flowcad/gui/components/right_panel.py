"""
Panneau propriétés équipement/connections selon choix
"""
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QBrush, QColor

from .mode_panels.equipment_panel import EquipmentPanel
from .mode_panels.connection_panel import ConnectionPanel
from.pump_dialog import CurveEditorDialog


class SelectiveEditTreeWidget(QTreeWidget):
    """
    QTreeWidget personnalisé avec contrôle d'édition par colonne
    et styles corrects pour l'édition.
    """
    
    # Signal émis quand une propriété est modifiée
    propertyChanged = pyqtSignal(str, str)  # nom_propriété, nouvelle_valeur
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_styles()
        self.current_editing_item = None
        
    def setup_styles(self):
        """Configure les styles pour le TreeWidget"""
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                alternate-background-color: #f1f3f4;
                color: #212529;
            }
            
            QTreeWidget::item {
                padding: 4px;
                border: none;
                min-height: 20px;
                color: #212529;
            }
            
            QTreeWidget::item:hover {
                background-color: #e8f0fe;
                color: #212529;
            }
            
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #212529;
            }
            
            /* Style pour l'éditeur de texte pendant l'édition */
            QTreeWidget QLineEdit {
                background-color: white;
                border: 2px solid #4285f4;
                border-radius: 3px;
                padding: 4px 6px;
                margin: 0px; /* Pour compenser la bordure */
                min-height: 20px;
                color: black;
                font-weight: normal;
                selection-background-color: #4285f4;
                selection-color: white;
            }
        """)
    
    def edit(self, index, trigger, event):
        """Contrôle l'édition et marque l'item en cours d'édition"""
        item = self.itemFromIndex(index)
        if not item:
            return False
            
        parent = item.parent()
        
        if parent and parent.text(0) == "Propriétés":
            if index.column() == 1:
                # Marquer l'item comme étant en cours d'édition
                self.current_editing_item = item
                print(f"🔓 Édition autorisée pour '{item.text(0)}', colonne Valeur")
                return super().edit(index, trigger, event)
            else:
                print(f"🔒 Édition refusée pour '{item.text(0)}', colonne Nom")
                return False
        
        print(f"🔒 Édition refusée pour '{item.text(0)}' (non éditable)")
        return False
    
    def commitData(self, editor):
        """Appelé quand l'édition est validée"""
        super().commitData(editor)
        
        if self.current_editing_item:
            # Émettre le signal de modification
            prop_name = self.current_editing_item.text(0)
            prop_value = self.current_editing_item.text(1)
            print(f"✅ Propriété modifiée: '{prop_name}' = '{prop_value}'")
            self.propertyChanged.emit(prop_name, prop_value)
            
            self.current_editing_item = None
    
    def closeEditor(self, editor, hint):
        """Appelé quand l'éditeur est fermé"""
        super().closeEditor(editor, hint)
        
        if self.current_editing_item:
            print(f"❌ Édition fermée pour '{self.current_editing_item.text(0)}'")
            self.current_editing_item = None
    
    def mousePressEvent(self, event):
        """Change le curseur sur les zones éditables"""
        index = self.indexAt(event.pos())
        
        if index.isValid():
            item = self.itemFromIndex(index)
            if self.is_item_editable(item, index.column()):
                self.setCursor(Qt.IBeamCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Change le curseur selon la zone survolée"""
        index = self.indexAt(event.pos())
        
        if index.isValid():
            item = self.itemFromIndex(index)
            if self.is_item_editable(item, index.column()):
                self.setCursor(Qt.IBeamCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def is_item_editable(self, item, column):
        """Vérifie si un item/colonne est éditable"""
        if not item:
            return False
            
        parent = item.parent()
        return parent and parent.text(0) == "Propriétés" and column == 1
    
    
    def get_editable_properties(self):
        """Retourne un dictionnaire des propriétés éditables"""
        properties = {}
        root = self.invisibleRootItem()
        
        for i in range(root.childCount()):
            top_item = root.child(i)
            if top_item.text(0) == "Propriétés":
                for j in range(top_item.childCount()):
                    prop_item = top_item.child(j)
                    original_name = prop_item.data(0, Qt.UserRole)  # Nom technique original
                    prop_name = prop_item.text(0)
                    if original_name == "curve_points":
                        # Récupérer la valeur cachée pour curve_points
                        prop_value = prop_item.data(1, Qt.UserRole)
                    else:
                        # Valeur normale pour les autres propriétés
                        prop_value = float(prop_item.text(1))  # temporaire, convertir en float
                    if original_name:
                        properties[original_name] = prop_value
                    else:
                        properties[prop_name] = prop_value
                break
                
        return properties
    
    def set_property_value(self, property_name, new_value):
        """Définit la valeur d'une propriété par son nom"""
        root = self.invisibleRootItem()
        
        for i in range(root.childCount()):
            top_item = root.child(i)
            if top_item.text(0) == "Propriétés":
                for j in range(top_item.childCount()):
                    prop_item = top_item.child(j)
                    if prop_item.text(0) == property_name:
                        prop_item.setText(1, str(new_value))
                        return True
                break
                
        return False


class RightPanel(QWidget):

    equipment_update_requested = pyqtSignal(str, dict)  # ID et dict des propriétés mises à jour
    pipe_update_requested = pyqtSignal(str, dict)       # ID et dict des propriétés mises à jour

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)  # Largeur fixe pour le panneau
        self.setStyleSheet(
            "background-color: #e8e8e8; "
            "border: 1px solid #ccc;"
            "border-right: 1px solid #ccc;")

        # Pour l'instant, juste un label
        self.setup_ui()

        self.selected_item_type = None  # "equipment" ou "pipe" ou None
    
    def setup_ui(self):
        """Configure le panneau équipement (vide pour l'instant)"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        #Le titre du panneau
        title_right_panel = QLabel("Propriétés")
        title_right_panel.setStyleSheet(
            "background-color: #e8e8e8;"   
            "color: black;"                
            "font-weight: bold;"        
            "font-size: 14px;"   
            "border: 1px solid #1B4F72;"   
            "padding: 4px;")

        
        title_right_panel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        title_right_panel.setFixedHeight(30)
        layout.addWidget(title_right_panel)

        # Créer le widget avec édition sélective
        self.properties_tree = SelectiveEditTreeWidget()
        self.properties_tree.setHeaderLabels(["Propriété", "Valeur"])
        self.properties_tree.setAlternatingRowColors(True)
        self.properties_tree.setRootIsDecorated(True)

        ## SUPPRIME L'INDENTATION
        self.properties_tree.setIndentation(0)

        # Connecter le signal pour traiter les modifications
        self.properties_tree.itemChanged.connect(self.on_property_changed)

        layout.addWidget(self.properties_tree)



        # Ajoute un "stretch" qui pousse le widget vers le haut
        #layout.addStretch()

        #un bouton "appliquer"
        button_apply = QPushButton("Appliquer")
        button_apply.setStyleSheet(
            "QPushButton {"
            "   background-color: #e8e8e8;"  # Gris clair
            "   color: black;"
            "   border: 1px solid #ccc;"
            "   padding: 10px;"
            "   text-align: center;"
            "   text-decoration: none;"
            "   font-size: 14px;"
            "   margin: 4px 2px;"
            "   border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "   background-color: #d7d7d7;"  # Gris plus foncé au survol
            "}"
        )
        layout.addWidget(button_apply)
        button_apply.clicked.connect(self.on_apply_clicked)

    def on_property_changed(self, item, column):
        """Gestionnaire des modifications de propriétés"""
        if self.properties_tree.is_item_editable(item, column):
            prop_name = item.text(0)
            new_value = item.text(1)
            print(f"📝 Propriété modifiée - {prop_name}: {new_value}")
            
            # Ici vous pouvez:
            # - Valider la nouvelle valeur
            # - Sauvegarder dans votre modèle de données
            # - Déclencher des mises à jour d'autres parties de l'interface
            # - Etc.

    def format_property_name(self, prop_name):
        """Convertit les noms de propriétés techniques en noms d'affichage"""
            
        # Dictionnaire de conversion des noms
        property_display_names = {
            'length_m': 'Longueur (m)',
            'diameter_m': 'Diamètre (m)', 
            'roughness_mm': 'Rugosité (mm)',
            'flow_rate_1': 'Débit 1 (m³/s)',
            'flow_rate_2': 'Débit 2 (m³/s)',
            'flow_rate_3': 'Débit 3 (m³/s)',
            'pressure_1': 'Pression 1 (kPa)',
            'pressure_2': 'Pression 2 (kPa)',
            'pressure_3': 'Pression 3 (kPa)',
            'head_1': 'Charge 1 (kPa)',
            'head_2': 'Charge 2 (kPa)',
            'head_3': 'Charge 3 (kPa)',
            'headloss': 'Perte de charge (Pa/m)',
            'total_headloss': 'Perte de charge totale (kPa)',
            'curve_points': 'Courbe de pompe (Q,P)',
            # Ajoutez d'autres mappings selon vos besoins
        }
            
        # Retourner le nom formaté s'il existe, sinon le nom original
        return property_display_names.get(prop_name, prop_name)

    def display_properties(self, properties_data, type="equipment"):
        """Affiche les propriétés d'un équipement ou vide le panneau"""
        self.properties_tree.clear()

        
        print(f"🔍 Propriétés reçues pour affichage: {properties_data}, type de données: {type}")

        if not properties_data:
            # Aucune sélection - panneau vide
            return
        
        if type not in ["equipment", "pipe"]:
            # Type inconnu - panneau vide
            return
        
        self.selected_item_type = type #le type de sélection 

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(10)  # Optionnel : taille légèrement plus grande
        
        # Propriétés générales------------------------------------------------
        general_item = QTreeWidgetItem(["Général", ""])
        general_item.setFont(0, bold_font)  # Colonne 0 en gras
        self.properties_tree.addTopLevelItem(general_item)
        QTreeWidgetItem(general_item, ["ID", properties_data.get('ID', '')])
        QTreeWidgetItem(general_item, ["Nom", properties_data.get('display_name', '')])
        QTreeWidgetItem(general_item, ["Description", properties_data.get('description', '')])
        QTreeWidgetItem(general_item, ["Classe", properties_data.get('equipment_class', '')])
        #QTreeWidgetItem(general_item, ["Couleur", properties_data.get('color', '')])
        general_item.setExpanded(True)

        properties_item = QTreeWidgetItem(["Propriétés", ""])
        properties_item.setFont(0, bold_font)  # Colonne 0 en gras

        #ajouter les propriétés dynamiques-----------------------------------------
        properties = properties_data.get('properties', {})
        for prop_name, prop_value in properties.items():
            display_name = self.format_property_name(prop_name)
            if prop_name == "curve_points":
                prop_item = QTreeWidgetItem(properties_item, [display_name, ""])  # Valeur vide
                
                # Créer le bouton
                curve_button = QPushButton("Éditer courbe...")
                curve_button.setToolTip(f"Points de courbe: {prop_value}")  # Info-bulle avec la valeur
                #conversion des valeurs
                list_of_tuples = [tuple(point) for point in prop_value]
                #print(f"🔄 Conversion des points de courbe pour le bouton: {list_of_tuples}")
                curve_button.clicked.connect(lambda: self.open_curve_editor(list_of_tuples))

                # Ajouter le bouton à la colonne "Valeur"
                self.properties_tree.setItemWidget(prop_item, 1, curve_button)
                
                # Stocker quand même la valeur originale pour récupération
                prop_item.setData(1, Qt.UserRole, prop_value)  # Valeur cachée dans colonne 1
                prop_item.setData(0, Qt.UserRole, prop_name)   # Nom technique original
                
            else:
                # CAS NORMAL : propriété éditable classique
                prop_item = QTreeWidgetItem(properties_item, [display_name, str(prop_value)])
                prop_item.setFlags(prop_item.flags() | Qt.ItemIsEditable)
                prop_item.setData(0, Qt.UserRole, prop_name)  # Nom technique original

        self.properties_tree.addTopLevelItem(properties_item)
        properties_item.setExpanded(True)

        results_item = QTreeWidgetItem(["Résultats", ""])
        results_item.setFont(0, bold_font)  # Colonne 0 en gras

        # Ajouter les résultats ------------------------------------------
        results = properties_data.get('results', {})
        for result_name, result_value in results.items():
            display_name = self.format_property_name(result_name)
            result_item = QTreeWidgetItem(results_item, [display_name, str(result_value)])
            # IMPORTANT: Stocker le nom original comme données cachées
            result_item.setData(0, Qt.UserRole, result_name)  # Nom technique original

        self.properties_tree.addTopLevelItem(results_item)
        results_item.setExpanded(True)

    #si on clique sur le bouton appliquer, mettre à jour les propriétés
    def on_apply_clicked(self):
        """Gestionnaire de clic pour le bouton Appliquer"""
        print("🔄 Mise à jour des propriétés...")
        # Ici, vous pouvez récupérer les valeurs des propriétés et les appliquer

        if self.selected_item_type not in ["equipment", "pipe"]:
            print("⚠️ Type d'élément non défini ou inconnu, aucune mise à jour effectuée.")
            return
        
        #si c'est un équipement
        if self.selected_item_type == "equipment":
            print("🔧 Mise à jour des propriétés de l'équipement sélectionné")
            equipment_id = self.get_main_id_from_tree()
            if not equipment_id:
                print("⚠️ Impossible de récupérer l'ID de l'équipement, aucune mise à jour effectuée.")
                return
            properties = self.properties_tree.get_editable_properties()
            print(f"🆔 ID Équipement: {equipment_id}")

            # Émettre le signal
            self.equipment_update_requested.emit(equipment_id, properties)

            # Récupérer les propriétés éditées
            
        elif self.selected_item_type == "pipe":
            print("🔧 Mise à jour des propriétés de la connexion (tuyau) sélectionnée")
            # Récupérer les propriétés éditées
            pipe_id = self.get_main_id_from_tree()
            if not pipe_id:
                print("⚠️ Impossible de récupérer l'ID de la connexion, aucune mise à jour effectuée.")
                return
            properties = self.properties_tree.get_editable_properties()
            print(f"🆔 ID Connexion: {pipe_id}")

            # Émettre le signal
            self.pipe_update_requested.emit(pipe_id, properties)

    def get_main_id_from_tree(self):
        """Récupère l'ID principal depuis l'arbre des propriétés"""
        root = self.properties_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "Général":
                for j in range(item.childCount()):
                    child = item.child(j)
                    if child.text(0) == "ID":
                        return child.text(1)
        return None
    
    def open_curve_editor(self, points):
        """Ouvre un éditeur de courbe (placeholder pour l'instant)"""
        print(f"✏️ Ouverture de l'éditeur de courbe avec points: {points}")
        # Ici, vous pouvez implémenter une vraie fenêtre d'édition de courbe
        # Pour l'instant, juste un message
        # Par exemple, ouvrir une nouvelle fenêtre modale avec un graphique interactif
        print("points:", points)
        dialog = CurveEditorDialog(curve_points=points, parent=self)

        results = dialog.exec_()

        if results == QDialog.Accepted:
            new_points = dialog.get_curve_points()
            print(f"✅ Nouveaux points de courbe obtenus: {new_points}")
            #temporaire: ajouter juste 1 point, le premier
            new_points = new_points[:1]
            self.update_curve_points(new_points)
        else:
            print("❌ Édition de la courbe annulée")    



    def update_curve_points(self, new_curve_points):
        """Met à jour les points de courbe dans l'arbre"""
        print(f"🔄 Mise à jour des points de courbe: {new_curve_points}")
        
        # Trouver l'item curve_points dans l'arbre et mettre à jour sa valeur cachée
        root = self.properties_tree.invisibleRootItem()
        for i in range(root.childCount()):
            top_item = root.child(i)
            if top_item.text(0) == "Propriétés":
                for j in range(top_item.childCount()):
                    prop_item = top_item.child(j)
                    original_name = prop_item.data(0, Qt.UserRole)
                    if original_name == "curve_points":
                        # Mettre à jour la valeur cachée
                        prop_item.setData(1, Qt.UserRole, new_curve_points)
                        
                        # Mettre à jour l'info-bulle du bouton
                        button = self.properties_tree.itemWidget(prop_item, 1)
                        if button:
                            button.setToolTip(f"Points de courbe: {new_curve_points}")
                        
                        print("✅ Points de courbe mis à jour dans l'interface")
                        return