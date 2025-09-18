# =============================================================================
# src/flowcad/file_io/file_manager.py
# =============================================================================
"""
Gestionnaire de sauvegarde et chargement des projets FlowCAD
"""

import json
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QPointF

def convert_to_serializable(obj):
    """
    Convertit récursivement un objet en types sérialisables JSON
    Version simple et robuste
    """
    
    if isinstance(obj, dict):
        return {str(k): convert_to_serializable(v) for k, v in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    elif isinstance(obj, QPointF):
        return {"x": float(obj.x()), "y": float(obj.y())}
    
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    
    else:
        # Convertir tout le reste en string
        return str(obj)

class FlowCADFileManager:
    """Gestionnaire de fichiers pour les projets FlowCAD"""
    
    # Version du format de fichier
    FILE_FORMAT_VERSION = "1.0"
    
    # Extension par défaut
    DEFAULT_EXTENSION = ".fcad"
    
    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.is_modified = False
    
    # =============================================================================
    # SAUVEGARDE
    # =============================================================================
    
    def save_project(self, canvas, file_path: str = None, metadata: Dict = None) -> bool:
        """
        Sauvegarde un projet FlowCAD
        
        Args:
            canvas: Le DrawingCanvas contenant les équipements et tuyaux
            file_path: Chemin de sauvegarde (optionnel)
            metadata: Métadonnées du projet (optionnel)
        
        Returns:
            True si la sauvegarde a réussi
        """
        try:
            # Utiliser le chemin courant si pas spécifié
            if file_path is None:
                file_path = self.current_file_path
            
            if file_path is None:
                raise ValueError("Aucun chemin de fichier spécifié")
            
            # S'assurer que l'extension est correcte
            if not file_path.endswith(self.DEFAULT_EXTENSION):
                file_path += self.DEFAULT_EXTENSION
            
            # Construire la structure JSON
            project_data = self._build_project_data(canvas, metadata)

            # SOLUTION SIMPLE : Convertir tout en types sérialisables
            project_data = convert_to_serializable(project_data)
            
            # Sauvegarder dans le fichier
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # Mettre à jour l'état
            self.current_file_path = file_path
            self.is_modified = False
            
            print(f"✅ Projet sauvegardé : {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
            return False
    
    def _build_project_data(self, canvas, metadata: Dict = None) -> Dict:
        """Construit la structure de données du projet"""
        
        # Métadonnées par défaut
        now = datetime.now().isoformat()
        default_metadata = {
            "created": now,
            "modified": now,
            "author": "FlowCAD User",
            "description": "Projet FlowCAD"
        }
        
        if metadata:
            default_metadata.update(metadata)
        
        # Extraire les données du canvas
        equipment_data = self._extract_equipment_data(canvas)
        pipes_data = self._extract_pipes_data(canvas)
        
        # Structure complète
        project_data = {
            "flowcad_project": {
                "version": self.FILE_FORMAT_VERSION,
                "metadata": default_metadata,
                "canvas": {
                    "view_settings": {
                        "zoom": 1.0,  # TODO: Récupérer du canvas
                        "center_x": 0.0,
                        "center_y": 0.0
                    }
                },
                "equipment": equipment_data,
                "pipes": pipes_data,
                "simulation": {
                    "last_run": None,
                    "status": "not_run",
                    "global_results": {}
                }
            }
        }
        
        return project_data
    
    def _extract_equipment_data(self, canvas) -> List[Dict]:
        """Extrait les données des équipements du canvas"""
        equipment_list = []
        
        for eq_id, eq_item in canvas.get_all_equipment().items():
            # Position
            pos = eq_item.pos()
            
            # Transformation
            transformation = {
                "rotation_angle": eq_item.rotation_angle,
                "mirror_h": eq_item.mirror_h,
                "mirror_v": eq_item.mirror_v,
                "scale": eq_item.item_scale
            }
            
            # États des ports
            ports_data = {}
            for port_id, port_item in eq_item.ports.items():
                ports_data[port_id] = {
                    "status": port_item.connection_status.value,
                    "connected_to": None  # TODO: Identifier le tuyau connecté
                }
            
            # Données complètes de l'équipement
            equipment_data = {
                "id": eq_id,
                "type": eq_item.equipment_type,
                "class": eq_item.equipment_def.get("equipment_class", "unknown"),
                "position": {
                    "x": pos.x(),
                    "y": pos.y()
                },
                "transformation": transformation,
                "definition": {
                    "display_name": eq_item.equipment_def.get("display_name", ""),
                    "description": eq_item.equipment_def.get("description", ""),
                    "equipment_class": eq_item.equipment_def.get("equipment_class", ""),
                    "color": eq_item.equipment_def.get("color", "#666666")
                },
                "properties": eq_item.equipment_def.get("properties", {}),
                "results": eq_item.equipment_def.get("results", {}),
                "ports": ports_data
            }
            
            equipment_list.append(equipment_data)
        
        return equipment_list
    
    def _extract_pipes_data(self, canvas) -> List[Dict]:
        """Extrait les données des tuyaux du canvas"""
        pipes_list = []
        
        for pipe_id, pipe_item in canvas.get_all_polylines().items():
            # Points de la polyligne
            points_data = []
            for point in pipe_item.points:
                points_data.append({
                    "x": point.x(),
                    "y": point.y()
                })
            
            # Connexions aux ports
            connections = {
                "start_port": None,
                "end_port": None
            }
            
            if pipe_item.start_port and pipe_item.start_port.parent_equipment:
                connections["start_port"] = {
                    "equipment_id": pipe_item.start_port.parent_equipment.equipment_id,
                    "port_id": pipe_item.start_port.port_id
                }
            
            if pipe_item.end_port and pipe_item.end_port.parent_equipment:
                connections["end_port"] = {
                    "equipment_id": pipe_item.end_port.parent_equipment.equipment_id,
                    "port_id": pipe_item.end_port.port_id
                }
            
            # Données complètes du tuyau
            pipe_data = {
                "id": pipe_id,
                "points": points_data,
                "connections": connections,
                "properties": pipe_item.pipe_def.get("properties", {}),
                "results": pipe_item.pipe_def.get("results", {})
            }
            
            pipes_list.append(pipe_data)
        
        return pipes_list
    
    # =============================================================================
    # CHARGEMENT
    # =============================================================================
    
    def load_project(self, file_path: str, canvas) -> bool:
        """
        Charge un projet FlowCAD
        
        Args:
            file_path: Chemin du fichier à charger
            canvas: Le DrawingCanvas où charger les éléments
        
        Returns:
            True si le chargement a réussi
        """
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Fichier introuvable : {file_path}")
            
            # Charger le JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Valider la structure
            if not self._validate_project_data(project_data):
                raise ValueError("Structure de fichier invalide")
            
            # Nettoyer le canvas actuel
            canvas.clear_all_equipment()
            
            # Charger les équipements
            self._load_equipment(project_data, canvas)
            
            # Charger les tuyaux
            self._load_pipes(project_data, canvas)
            
            # Mettre à jour l'état
            self.current_file_path = file_path
            self.is_modified = False
            
            print(f"✅ Projet chargé : {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement : {e}")
            return False
    
    def _validate_project_data(self, data: Dict) -> bool:
        """Valide la structure des données du projet"""
        try:
            # Vérifications de base
            if "flowcad_project" not in data:
                return False
            
            project = data["flowcad_project"]
            
            # Version compatible
            version = project.get("version", "0.0")
            if version != self.FILE_FORMAT_VERSION:
                print(f"⚠️ Version différente : {version} vs {self.FILE_FORMAT_VERSION}")
            
            # Sections requises
            required_sections = ["equipment", "pipes", "metadata"]
            for section in required_sections:
                if section not in project:
                    print(f"❌ Section manquante : {section}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur validation : {e}")
            return False
    
    def _load_equipment(self, project_data: Dict, canvas) -> None:
        """Charge les équipements dans le canvas"""
        equipment_list = project_data["flowcad_project"].get("equipment", [])
        
        for eq_data in equipment_list:
            try:
                # Position
                pos = QPointF(
                    eq_data["position"]["x"],
                    eq_data["position"]["y"]
                )
                
                # Définition d'équipement pour le canvas
                equipment_def = {
                    "display_name": eq_data["definition"]["display_name"],
                    "description": eq_data["definition"]["description"],
                    "equipment_class": eq_data["definition"]["equipment_class"],
                    "color": eq_data["definition"]["color"],
                    "properties": eq_data["properties"],
                    "results": eq_data["results"]
                }
                
                # Créer l'équipement dans le canvas
                equipment_id = canvas.add_equipment(
                    eq_data["type"], 
                    equipment_def, 
                    pos
                )

                # donner l'ID correct
                unique_id = eq_data["id"]
                print(f"Renommer équipement {equipment_id} en {unique_id}")
                canvas.equipment_items[unique_id] = canvas.equipment_items.pop(equipment_id)
                canvas.equipment_items[unique_id].equipment_id = unique_id
                equipment_id = unique_id

                #change le parent de chaque port
                for port in canvas.equipment_items[equipment_id].ports.values():
                    port.setParentItem(canvas.equipment_items[equipment_id])

                # Appliquer les transformations
                equipment_item = canvas.get_equipment(equipment_id)
                if equipment_item:
                    transform = eq_data.get("transformation", {})
                    
                    # Échelle
                    if "scale" in transform:
                        equipment_item.set_item_scale(transform["scale"])
                    
                    # Rotation
                    if "rotation_angle" in transform:
                        equipment_item.set_rotation_angle(transform["rotation_angle"])
                    
                    # Miroirs
                    if transform.get("mirror_h", False):
                        equipment_item.set_mirror_direction("h")
                    if transform.get("mirror_v", False):
                        equipment_item.set_mirror_direction("v")
                
                print(f"✅ Équipement chargé : {equipment_id}")
                
            except Exception as e:
                print(f"❌ Erreur chargement équipement {eq_data.get('id', 'unknown')} : {e}")
    
    def _load_pipes(self, project_data: Dict, canvas) -> None:
        """Charge les tuyaux dans le canvas"""
        pipes_list = project_data["flowcad_project"].get("pipes", [])
        
        for pipe_data in pipes_list:
            try:
                # Points de la polyligne
                points = []
                for point_data in pipe_data["points"]:
                    points.append(QPointF(point_data["x"], point_data["y"]))
                
                # Trouver les ports de connexion
                start_port = None
                end_port = None
                
                start_conn = pipe_data["connections"].get("start_port")
                if start_conn:
                    eq_item = canvas.get_equipment(start_conn["equipment_id"])
                    if eq_item:
                        start_port = eq_item.get_port(start_conn["port_id"])
                
                end_conn = pipe_data["connections"].get("end_port")
                if end_conn:
                    eq_item = canvas.get_equipment(end_conn["equipment_id"])
                    if eq_item:
                        end_port = eq_item.get_port(end_conn["port_id"])
                
                # Créer la polyligne
                from ..gui.graphics.polyline_graphics import PolylineGraphicsItem
                polyline = PolylineGraphicsItem(
                    points, 
                    start_port, 
                    end_port, 
                    pipe_data["id"]
                )
                
                # Appliquer les propriétés
                if "properties" in pipe_data:
                    polyline.update_properties(pipe_data["properties"])
                
                # Ajouter au canvas
                canvas.scene.addItem(polyline)
                canvas.polylines[pipe_data["id"]] = polyline
                
                # Mettre à jour les statuts des ports
                if start_port:
                    from ..gui.graphics.equipment_graphics import PortConnectionStatus
                    start_port.set_connection_status(PortConnectionStatus.CONNECTED)
                if end_port:
                    end_port.set_connection_status(PortConnectionStatus.CONNECTED)
                
                print(f"✅ Tuyau chargé : {pipe_data['id']}")
                
            except Exception as e:
                print(f"❌ Erreur chargement tuyau {pipe_data.get('id', 'unknown')} : {e}")
    
    # =============================================================================
    # UTILITAIRES
    # =============================================================================
    
    def get_current_file_path(self) -> Optional[str]:
        """Retourne le chemin du fichier actuel"""
        return self.current_file_path
    
    def set_modified(self, modified: bool = True):
        """Marque le projet comme modifié"""
        self.is_modified = modified
    
    def is_project_modified(self) -> bool:
        """Vérifie si le projet a été modifié"""
        return self.is_modified
    
    def get_project_name(self) -> str:
        """Retourne le nom du projet (sans extension)"""
        if self.current_file_path:
            return Path(self.current_file_path).stem
        return "Nouveau projet"
    
    def create_backup(self, canvas) -> bool:
        """Crée une sauvegarde automatique"""
        if not self.current_file_path:
            return False
        
        try:
            # Nom du fichier de backup
            backup_path = self.current_file_path.replace(
                self.DEFAULT_EXTENSION, 
                f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{self.DEFAULT_EXTENSION}"
            )
            
            return self.save_project(canvas, backup_path)
            
        except Exception as e:
            print(f"❌ Erreur création backup : {e}")
            return False