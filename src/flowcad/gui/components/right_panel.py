"""
Panneau propriétés équipement/connections selon choix
"""
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QSlider
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QBrush, QColor

from .mode_panels.equipment_panel import EquipmentPanel
from .mode_panels.connection_panel import ConnectionPanel
from.pump_dialog import CurveEditorDialog

from ...core.unit_manager import UnitManager, FlowUnit, PressureUnit


class SelectiveEditTreeWidget(QTreeWidget):
    """
    QTreeWidget personnalisé avec contrôle d'édition par colonne
    et styles corrects pour l'édition.
    """
    
    # Signal émis quand une propriété est modifiée
    propertyChanged = pyqtSignal(str, str)  # nom_propriété, nouvelle_valeur
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unit_mgr = UnitManager()
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

                    if original_name == "valve_control_type":
                        # Ne pas inclure cette propriété
                        continue

                    if original_name == "curve_points":
                        # Récupérer la valeur cachée pour curve_points
                        prop_value = prop_item.data(1, Qt.UserRole)
                    elif original_name == "opening_value":
                        # Récupérer la valeur du slider pour opening_value
                        valve_widget = self.itemWidget(prop_item, 1)
                        prop_value = valve_widget.get_value() if valve_widget else 0
                        print(f"Valeur du slider pour 'opening_value': {prop_value}")
                    elif original_name == "flow_rate_m3s":
                        # Reconvertir depuis l'unité utilisateur vers m³/s
                        prop_value = self.unit_mgr.input_flow_to_m3s(float(prop_item.text(1)))
                    else:
                        # Valeur normale pour les autres propriétés
                        prop_value = float(prop_item.text(1))  # temporaire, convertir en float
                    if original_name:
                        properties[original_name] = prop_value

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
        self.unit_mgr = UnitManager()
        self.setFixedWidth(300)  # Largeur fixe pour le panneau
        self.setStyleSheet(
            "background-color: #e8e8e8; "
            "border: 1px solid #ccc;"
            "border-right: 1px solid #ccc;")

        

        # Pour l'instant, juste un label
        self.setup_ui()

        self.selected_item_type = None  # "equipment" ou "pipe" ou None

        # Référence au canvas (sera définie par main_window)
        self._drawing_canvas = None
    
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
            'flow_rate': f"Débit {self.unit_mgr.get_flow_unit_symbol()}",
            'flow_rate_1': f"Débit 1 {self.unit_mgr.get_flow_unit_symbol()}",
            'flow_rate_2': f"Débit 2 {self.unit_mgr.get_flow_unit_symbol()}",
            'flow_rate_3': f"Débit 3 {self.unit_mgr.get_flow_unit_symbol()}",
            'pressure_1': f"Pression 1 {self.unit_mgr.get_pressure_unit_symbol()}",
            'pressure_2': f"Pression 2 {self.unit_mgr.get_pressure_unit_symbol()}",
            'pressure_3': f"Pression 3 {self.unit_mgr.get_pressure_unit_symbol()}",
            'head_1': f"Charge 1 {self.unit_mgr.get_pressure_unit_symbol()}",
            'head_2': f"Charge 2 {self.unit_mgr.get_pressure_unit_symbol()}",
            'head_3': f"Charge 3 {self.unit_mgr.get_pressure_unit_symbol()}",
            'headloss': f"Perte de charge Pa/m",
            'head_gain': f"Gain de charge {self.unit_mgr.get_pressure_unit_symbol()}",
            'total_headloss': f"Perte de charge totale {self.unit_mgr.get_pressure_unit_symbol()}",
            'curve_points': 'Courbe de pompe (Q,P)',
            'velocity': 'vitesse (m/s)',
            'opening_value': 'État d\'ouverture',
            'valve_control_type': 'Type de contrôle de vanne',
            'flow_rate_m3s': f"Débit {self.unit_mgr.get_flow_unit_symbol()}",
            # Ajoutez d'autres mappings selon vos besoins
        }
            
        # Retourner le nom formaté s'il existe, sinon le nom original
        return property_display_names.get(prop_name, prop_name)
    
    def is_pressure_property(self, prop_name: str) -> bool:
        """Détermine si une propriété est une pression"""
        pressure_keywords = [
            'pressure',
            'pressure_1', 'pressure_2', 'pressure_3',
            'head_1', 'head_2', 'head_3',
            'total_headloss'
        ]
        
        prop_name_lower = prop_name.lower()
    
        # Correspondance exacte OU contient des patterns spécifiques
        if prop_name_lower in pressure_keywords:
            return True

        #return any(keyword in prop_name_lower for keyword in pressure_keywords)
    
    def is_flow_property(self, prop_name: str) -> bool:
        """Détermine si une propriété est un débit"""
        flow_keywords = [
            'flow', 'flowrate', 'debit', 'débit',
            'flow_rate', 'flowrate_m3s', 'volume_flow'
        ]

        prop_name_lower = prop_name.lower()
        return any(keyword in prop_name_lower for keyword in flow_keywords)

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
            if prop_name == "flow_rate_m3s":
                # Convertir depuis m³/s vers l'unité utilisateur
                prop_value_display = self.unit_mgr.display_flow(float(prop_value))
                prop_item = QTreeWidgetItem(properties_item, [display_name, str(prop_value_display)])
                prop_item.setFlags(prop_item.flags() | Qt.ItemIsEditable)
                prop_item.setData(0, Qt.UserRole, prop_name)  # Nom technique original
            elif prop_name == "curve_points":
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
            elif prop_name == "opening_value":
                prop_item = QTreeWidgetItem(properties_item, [display_name, ""])  # Valeur vide
                # Lire le type depuis les propriétés
                valve_control_type = properties_data.get('properties', {}).get('valve_control_type', 'proportional')
                
                # Fallback si valve_control_type n'existe pas
                if valve_control_type not in ['binary', 'proportional']:
                    equipment_class = properties_data.get('equipment_class', '')
                    valve_control_type = "binary" if equipment_class in ["ball_valve", "gate_valve", "check_valve"] else "proportional"
                
                print(f"🎛️ Type de contrôle vanne: {valve_control_type}")
                
                # Créer le widget avec le bon type
                valve_widget = ValveStateWidget(prop_value, valve_type=valve_control_type)
                
                self.properties_tree.setItemWidget(prop_item, 1, valve_widget)
                prop_item.setData(1, Qt.UserRole, prop_value)
                prop_item.setData(0, Qt.UserRole, prop_name)  
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
            print(f"🔢 Traitement du résultat: {result_name} = {result_value}")
            if self.is_pressure_property(result_name):
                result_value =self.unit_mgr.format_pressure(float(result_value))
            elif self.is_flow_property(result_name):
                result_value = self.unit_mgr.format_flow(float(result_value))
            elif result_name in ['headloss']:
                result_value = f"{float(result_value):.2f} Pa/m"
            elif result_name in ['velocity']:
                result_value = f"{float(result_value):.2f} m/s"
            elif result_name in ['head_gain']:
                result_value = self.unit_mgr.format_pressure(float(result_value))
            else:
                result_value = f"{float(result_value):.2f}"
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


            #  Programmer un rafraîchissement après un court délai
            QTimer.singleShot(100, lambda: self._refresh_current_display("equipment", equipment_id))

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

            #  Programmer un rafraîchissement après un court délai
            QTimer.singleShot(100, lambda: self._refresh_current_display("pipe", pipe_id))

    def set_drawing_canvas(self, canvas):
        """Définit la référence au drawing_canvas"""
        self._drawing_canvas = canvas
        print("📋 Référence au drawing_canvas configurée dans RightPanel")

    def _refresh_current_display(self, item_type, item_id):
        """Rafraîchit l'affichage actuel avec les données mises à jour"""
        print(f"🔄 Rafraîchissement automatique pour {item_type} {item_id}")
        
        # Récupérer les données mises à jour depuis main_window
        if not self._drawing_canvas:
            print("⚠️ Référence au drawing_canvas manquante")
            return

        if item_type == "equipment":
            equipment_item = self._drawing_canvas.get_equipment(item_id)
            if equipment_item:
                self.display_properties(equipment_item.equipment_def, "equipment")
                print("✅ Affichage rafraîchi pour l'équipement")
        elif item_type == "pipe":
            pipe_item = self._drawing_canvas.get_pipe(item_id)
            if pipe_item:
                self.display_properties(pipe_item.pipe_def, "pipe")
                print("✅ Affichage rafraîchi pour la connexion (tuyau)")

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
            new_points = dialog.export_curve_points()
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

#==============================================================================                   
# Créer une classe pour le widget slider personnalisé
# Dans right_panel.py - Version modifiée du ValveStateWidget

class ValveStateWidget(QWidget):
    """Widget personnalisé pour afficher et modifier l'état d'une vanne"""
    
    def __init__(self, initial_value, valve_type="proportional", callback=None, parent=None):
        super().__init__(parent)
        self.valve_type = valve_type  # "binary" ou "proportional"
        self.callback = callback
        self.setup_ui(initial_value)
    
    def setup_ui(self, initial_value):
        """Configure l'interface du widget slider"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Slider horizontal
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        
        # Définir la valeur initiale
        initial_val = int(float(initial_value)) if isinstance(initial_value, (str, int, float)) else 50
        
        # ⭐ NOUVEAU : Pour les vannes binaires, forcer 0 ou 100
        if self.valve_type == "binary":
            initial_val = 100 if initial_val >= 50 else 0
        
        self.slider.setValue(initial_val)
        
        # Style du slider (identique)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:1 #44ff44);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #999999;
                width: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                border: 2px solid #555555;
            }
        """)
        
        # Label pour afficher la valeur
        self.value_label = QLabel()
        self.value_label.setMinimumWidth(60)
        self.value_label.setAlignment(Qt.AlignCenter)
        
        # ⭐ NOUVEAU : Connecter différents signaux selon le type de vanne
        if self.valve_type == "binary":
            # Pour les vannes binaires : snap à 0 ou 100 dès qu'on bouge
            self.slider.sliderMoved.connect(self.snap_to_binary)
            self.slider.valueChanged.connect(self.update_label)
        else:
            # Pour les vannes proportionnelles : comportement normal
            self.slider.valueChanged.connect(self.update_label)
        
        # Mise à jour initiale du label
        self.update_label(self.slider.value())
        
        # Ajouter les widgets au layout
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label, 0)
    
    def snap_to_binary(self, value):
        """Force le slider à se positionner sur 0 ou 100 uniquement"""
        if value < 50:
            snap_value = 0
        else:
            snap_value = 100
        
        # Mise à jour sans déclencher le signal sliderMoved
        self.slider.blockSignals(True)
        self.slider.setValue(snap_value)
        self.slider.blockSignals(False)
        
        # Déclencher manuellement la mise à jour du label
        self.update_label(snap_value)
        
        # Appeler le callback si défini
        if self.callback:
            self.callback(snap_value)
    
    def update_label(self, value):
        """Met à jour le texte du label selon la valeur du slider"""
        if self.valve_type == "binary":
            # Pour les vannes binaires : seulement "Fermé" ou "Ouvert"
            if value <= 50:
                text = "Fermé"
                color = "#ff4444"
            else:
                text = "Ouvert"
                color = "#44ff44"
        else:
            # Pour les vannes proportionnelles : comportement original
            if value <= 5:
                text = "Fermé"
                color = "#ff4444"
            elif value >= 95:
                text = "Ouvert" 
                color = "#44ff44"
            else:
                text = f"{value}%"
                color = "#ffaa00"
        
        self.value_label.setText(text)
        #self.value_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def get_value(self):
        """Retourne la valeur actuelle du slider"""
        return self.slider.value()
    
    def set_value(self, value):
        """Définit la valeur du slider"""
        val = int(float(value)) if isinstance(value, (str, int, float)) else 50
        
        # Pour les vannes binaires, forcer 0 ou 100
        if self.valve_type == "binary":
            val = 100 if val >= 50 else 0
            
        self.slider.setValue(val)