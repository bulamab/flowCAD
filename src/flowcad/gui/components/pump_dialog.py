"""
Dialogue d'édition des points de courbe débit/pression
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QWidget, QHeaderView)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scipy.optimize import curve_fit
from ...core.unit_manager import UnitManager, PressureUnit, FlowUnit


class CurveEditorDialog(QDialog):
    """
    Dialogue pour éditer les points de courbe débit/pression
    """
    
    def __init__(self, curve_points=None, parent=None):
        super().__init__(parent)
        self.curve_points = curve_points or [(0.001, 133), (1, 100), (2, 0)]  # Valeurs par défaut
        self.nbre_of_points = len(self.curve_points)
        self.coefficients = {'A': 0, 'B': 0, 'C': 2}  # Coefficients de l'équation h = A - Bq^C
        self.unit_mgr = UnitManager.get_instance()
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Éditeur de courbe débit/pression")
        self.setModal(True)
        self.resize(800, 600)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        
        # === PANNEAU GAUCHE ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(300)
        
        # Menu déroulant pour le nombre de points
        points_label = QLabel("Nombre de points:")
        self.points_combo = QComboBox()
        self.points_combo.addItems(["1 point", "3 points"])
        if self.nbre_of_points == 1:
            self.points_combo.setCurrentText("1 point")
        else:
            self.points_combo.setCurrentText("3 points")

        left_layout.addWidget(points_label)
        left_layout.addWidget(self.points_combo)
        
        # Tableau des points
        table_label = QLabel("Points de la courbe:")
        self.points_table = QTableWidget()
        self.points_table.setColumnCount(2)
        self.points_table.setHorizontalHeaderLabels([f"Débit ({self.unit_mgr.get_flow_unit_symbol()})", f"Pression ({self.unit_mgr.get_pressure_unit_symbol()})"])
        
        # Ajuster la largeur des colonnes
        header = self.points_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        left_layout.addWidget(table_label)
        left_layout.addWidget(self.points_table)
        
        
        # Stretch pour pousser vers le haut
        left_layout.addStretch()
        
        # Boutons OK/Annuler
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Annuler")
        
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)
        left_layout.addLayout(dialog_buttons)
        
        # === PANNEAU DROIT - GRAPHIQUE ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Créer le graphique matplotlib
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        right_layout.addWidget(self.canvas)
        
        # Ajouter les panneaux au layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
    def setup_connections(self):
        """Configure les connexions des signaux"""
        # Connexions des boutons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        # Connexion du combo box
        self.points_combo.currentTextChanged.connect(self.on_points_count_changed)
        
        # Connexion du tableau pour mise à jour du graphique
        self.points_table.itemChanged.connect(self.on_table_changed)
        
    def load_initial_data(self):
        """Charge les données initiales dans le tableau"""
        self.populate_table()
        self.calculate_coefficients()  # Calculer les coefficients initiaux
        self.update_graph()
        
    def populate_table(self):
        """Remplit le tableau avec les points actuels"""
        self.points_table.setRowCount(len(self.curve_points))
        
        for row, (flow, pressure) in enumerate(self.curve_points):
            # Colonne débit
            flow_item = QTableWidgetItem(str(self.unit_mgr.display_flow(flow)))
            flow_item.setFlags(flow_item.flags() | Qt.ItemIsEditable)
            self.points_table.setItem(row, 0, flow_item)

            # Colonne pression
            pressure_item = QTableWidgetItem(str(self.unit_mgr.display_pressure(pressure)))
            pressure_item.setFlags(pressure_item.flags() | Qt.ItemIsEditable)
            self.points_table.setItem(row, 1, pressure_item)

    def on_table_changed(self):
        """Gestionnaire quand le tableau change"""
        self.calculate_coefficients()  # Recalculer automatiquement
        self.update_graph()
            
    def update_graph(self):
        """Met à jour le graphique avec les données du tableau"""
        # Récupérer les données du tableau
        flows = []
        pressures = []
        
        for row in range(self.points_table.rowCount()):
            try:
                flow_item = self.points_table.item(row, 0)
                pressure_item = self.points_table.item(row, 1)
                
                if flow_item and pressure_item:
                    flow = float(flow_item.text())
                    pressure = float(pressure_item.text())
                    flows.append(flow)
                    pressures.append(pressure)
            except ValueError:
                # Ignorer les valeurs non numériques
                continue
        
        # Nettoyer et redessiner le graphique
        self.ax.clear()
        
        if flows and pressures:
            # Tracer les points
            self.ax.scatter(flows, pressures, color='red', s=50, zorder=5)
            
            # Tracer la courbe si plus d'un point
            # Tracer la courbe théorique si les coefficients sont disponibles
            if self.coefficients['A'] != 0 or self.coefficients['B'] != 0:
                # Générer une courbe lisse
                q_min = 0
                q_max = max(flows) * 2.2 if flows else 2.0
                q_curve = np.linspace(q_min, q_max, 100)
                
                try:
                    h_curve = self.pump_equation(q_curve, self.coefficients['A'], 
                                            self.coefficients['B'], self.coefficients['C'])
                    
                    # Ne tracer que les valeurs positives de h
                    valid_indices = h_curve >= 0
                    q_valid = q_curve[valid_indices]
                    h_valid = h_curve[valid_indices]
                    
                    if len(q_valid) > 0:
                        self.ax.plot(q_valid, h_valid, 'b-', linewidth=2, 
                                label=f'h = {self.coefficients["A"]:.2f} - {self.coefficients["B"]:.2f}q^{self.coefficients["C"]:.2f}')
                except:
                    pass  # En cas d'erreur dans le calcul, ignorer la courbe théorique
        
        # Configuration du graphique
        self.ax.set_xlabel(f'Débit ({self.unit_mgr.get_flow_unit_symbol()})')
        self.ax.set_ylabel(f'Pression ({self.unit_mgr.get_pressure_unit_symbol()})')
        self.ax.set_title('Courbe débit/pression')
        self.ax.grid(True, alpha=0.3)
        
        # Redessiner
        self.canvas.draw()
        
    def on_points_count_changed(self, text):
        """Gestionnaire du changement du nombre de points"""
        # Extraire le nombre de points
        if "1 point" in text:
            target_count = 1
        elif "3 points" in text:
            target_count = 3
            
        self.adjust_points_count(target_count)
        
    def adjust_points_count(self, target_count):
        """Ajuste le nombre de points dans le tableau"""
        current_count = self.points_table.rowCount()
        
        if target_count > current_count:
            # Ajouter des points
            for i in range(current_count, target_count):
                self.points_table.setRowCount(i + 1)
                # Valeurs par défaut pour nouveaux points
                flow_item = QTableWidgetItem("0.0")
                pressure_item = QTableWidgetItem("0.0")
                self.points_table.setItem(i, 0, flow_item)
                self.points_table.setItem(i, 1, pressure_item)
        elif target_count < current_count:
            # Supprimer des points
            self.points_table.setRowCount(target_count)
            
        self.update_graph()
        
    def get_curve_points(self):
        """Retourne les points de courbe actuels sous forme de liste de tuples"""
        points = []
        for row in range(self.points_table.rowCount()):
            try:
                flow_item = self.points_table.item(row, 0)
                pressure_item = self.points_table.item(row, 1)
                
                if flow_item and pressure_item:
                    flow = (float(flow_item.text()))
                    pressure = (float(pressure_item.text()))
                    points.append((flow, pressure))
            except ValueError:
                # Ignorer les valeurs invalides
                continue
                
        #pour le cas ou il y a un seul point, on ajoute des points par defaut
        if len(points) == 1:
            points.append((0, points[0][1]*1.33))  # point à débit 0
            points.append((2*points[0][0], 0))     # point à pression 0
        return points
    
    def export_curve_points(self):
        """Retourne les points de courbe formatés pour l'export"""
        raw_points = self.get_curve_points()
        # Convertir les points en unités de base (m3/s, Pa)
        converted_points = []
        for flow, pressure in raw_points:
            flow_base = self.unit_mgr.input_flow_to_m3s(flow)
            pressure_base = self.unit_mgr.input_pressure_to_pa(pressure)
            converted_points.append((flow_base, pressure_base))
        return converted_points
        
    def set_curve_points(self, points):
        """Définit les points de courbe à afficher"""
        self.curve_points = points
        self.populate_table()
        self.calculate_coefficients()
        self.update_graph()

    def pump_equation(self, q, A, B, C):
        """Équation de la pompe: h = A - Bq^C"""
        return A - B * np.power(q, C)

    def calculate_coefficients(self):
        """Calcule les coefficients A, B, C de l'équation h = A - Bq^C"""
        try:
            # Récupérer les points du tableau
            points = self.get_curve_points()
            
            if len(points) < 3:
                print("⚠️ Au moins 3 points sont nécessaires pour calculer les coefficients")
                return
            
            # Séparer q (débits) et h (hauteurs)
            q_data = np.array([point[0] for point in points])
            h_data = np.array([point[1] for point in points])
            
            # Éviter les débits nuls pour éviter les problèmes avec les puissances
            if np.any(q_data <0):
                print("⚠️ Les débits doivent être strictement positifs")
                return
            
            # Estimation initiale des paramètres
            A_init = max(h_data) * 1.1  # A légèrement supérieur à la hauteur max
            B_init = A_init / (max(q_data) ** 2)  # Estimation basée sur un exposant de 2
            C_init = 2.0  # Exposant initial typique pour les pompes
            
            # Ajustement de courbe avec scipy
            popt, pcov = curve_fit(
                self.pump_equation, 
                q_data, 
                h_data, 
                p0=[A_init, B_init, C_init],
                bounds=([0, 0, 0.5], [np.inf, np.inf, 5.0])  # Contraintes raisonnables
            )
            
            # Stocker les coefficients
            self.coefficients['A'] = popt[0]
            self.coefficients['B'] = popt[1]
            self.coefficients['C'] = popt[2]
            
            
            # Calculer la qualité de l'ajustement (R²)
            h_pred = self.pump_equation(q_data, *popt)
            ss_res = np.sum((h_data - h_pred) ** 2)
            ss_tot = np.sum((h_data - np.mean(h_data)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            print(f"✅ Coefficients calculés:")
            print(f"   A = {self.coefficients['A']:.4f}")
            print(f"   B = {self.coefficients['B']:.4f}")
            print(f"   C = {self.coefficients['C']:.4f}")
            print(f"   R² = {r_squared:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur dans le calcul des coefficients: {e}")
            # Réinitialiser les coefficients en cas d'erreur
            self.coefficients = {'A': 0, 'B': 0, 'C': 2}