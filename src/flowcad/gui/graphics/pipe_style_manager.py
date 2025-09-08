# Créer un nouveau fichier: src/flowcad/gui/graphics/pipe_style_manager.py

"""
Gestionnaire de styles pour synchroniser l'apparence des tuyaux 
entre les polylignes et les éléments SVG des équipements
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import QObject, pyqtSignal

class PipeStyleManager(QObject):
    """Gestionnaire central des styles de tuyaux"""
    
    # Signal émis quand les styles changent
    styles_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Styles par défaut des tuyaux (synchronisés avec polyline_graphics.py)
        self.pipe_styles = {
            'normal': {
                'stroke': '#4682B4',  # Bleu acier
                'stroke-width': '4',
                'fill': 'none',
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round'
            },
            'selected': {
                'stroke': '#FF8C00',  # Orange
                'stroke-width': '4',
                'fill': 'none',
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round'
            },
            'hover': {
                'stroke': '#1E90FF',  # Bleu dodger
                'stroke-width': '4',
                'fill': 'none',
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round'
            }
        }
        
        # Cache des SVG modifiés
        self.modified_svg_cache: Dict[str, str] = {}
    
    def get_pipe_style(self, state: str = 'normal') -> Dict[str, str]:
        """Retourne le style des tuyaux pour un état donné"""
        return self.pipe_styles.get(state, self.pipe_styles['normal']).copy()
    
    def set_pipe_style(self, state: str, **style_attrs):
        """Modifie le style des tuyaux pour un état donné"""
        if state not in self.pipe_styles:
            self.pipe_styles[state] = {}
        
        self.pipe_styles[state].update(style_attrs)
        
        # Vider le cache car les styles ont changé
        self.modified_svg_cache.clear()
        
        # Notifier les changements
        self.styles_changed.emit()
        print(f"🎨 Style tuyau '{state}' mis à jour: {style_attrs}")
    
    def apply_pipe_styles_to_svg(self, svg_path: str, state: str = 'normal', scale_factor: float = 1.0) -> str:
        """
        Applique les styles de tuyaux aux éléments Pipexxx dans un SVG
        
        Args:
            svg_path: Chemin vers le fichier SVG
            state: État visuel ('normal', 'selected', 'hover')
            scale_factor: Facteur d'échelle de l'équipement (pour ajuster stroke-width)
        
        Returns:
            Contenu SVG modifié avec styles appliqués
        """
        cache_key = f"{svg_path}:{state}:{scale_factor:.3f}"
        
        # Vérifier le cache
        if cache_key in self.modified_svg_cache:
            return self.modified_svg_cache[cache_key]
        
        # Lire le fichier SVG
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception as e:
            print(f"❌ Erreur lecture SVG {svg_path}: {e}")
            return ""
        
        # Modifier le SVG avec le facteur d'échelle
        modified_svg = self.modify_svg_pipe_elements(svg_content, state, scale_factor)
        
        # Mettre en cache
        self.modified_svg_cache[cache_key] = modified_svg
        
        return modified_svg
    
    def modify_svg_pipe_elements(self, svg_content: str, state: str, scale_factor: float = 1.0) -> str:
        """Modifie les éléments Pipexxx dans le contenu SVG avec ajustement d'échelle"""
        try:
            # Parser le XML
            root = ET.fromstring(svg_content)
            
            # Obtenir les styles à appliquer avec ajustement d'échelle
            pipe_style = self.get_scaled_pipe_style(state, scale_factor)
            
            # Rechercher tous les éléments avec ID contenant "Pipe"
            pipe_elements = self.find_pipe_elements(root)
            
            print(f"🔍 Trouvé {len(pipe_elements)} éléments Pipe (échelle: {scale_factor:.3f})")
            
            # Appliquer les styles
            for element in pipe_elements:
                self.apply_style_to_element(element, pipe_style)
            
            # Reconvertir en string
            return ET.tostring(root, encoding='unicode')
            
        except ET.ParseError as e:
            print(f"❌ Erreur parsing SVG: {e}")
            return svg_content  # Retourner l'original en cas d'erreur

    def get_scaled_pipe_style(self, state: str = 'normal', scale_factor: float = 1.0) -> Dict[str, str]:
        """
        Retourne le style des tuyaux avec épaisseurs ajustées selon l'échelle
        
        Args:
            state: État visuel
            scale_factor: Facteur d'échelle (< 1.0 = réduction, > 1.0 = agrandissement)
        
        Returns:
            Style avec stroke-width ajusté
        """
        base_style = self.pipe_styles.get(state, self.pipe_styles['normal']).copy()
        
        # Ajuster stroke-width selon l'échelle
        if 'stroke-width' in base_style and scale_factor > 0:
            original_width = float(base_style['stroke-width'])
            
            # Calcul de l'épaisseur effective
            # Si l'échelle est petite (< 1), on veut garder une épaisseur minimale visible
            # Si l'échelle est grande (> 1), on peut réduire proportionnellement
            
            if scale_factor < 1.0:
                # Pour les petites échelles : épaisseur inversement proportionnelle mais avec minimum
                adjusted_width = original_width / scale_factor
                # Limiter à une épaisseur maximale raisonnable
                adjusted_width = min(adjusted_width, original_width * 3)
                
            else:
                # Pour les échelles normales/grandes : proportionnel direct
                adjusted_width = original_width / scale_factor
            
            # Garantir une épaisseur minimale pour la visibilité
            adjusted_width = max(adjusted_width, 0.5)

            base_style['stroke-width'] = f"{adjusted_width:.2f}"
            
            print(f"📏 Ajustement stroke-width: {original_width} → {adjusted_width:.2f} (échelle: {scale_factor:.3f})")
        
        return base_style
    
    '''def calculate_optimal_stroke_width(self, base_width: float, scale_factor: float) -> float:
        """
        Calcule l'épaisseur optimale selon l'échelle
        
        Stratégies possibles:
        1. Inversement proportionnel: width / scale
        2. Racine carrée: width / sqrt(scale) 
        3. Logarithmique: width / log(scale + 1)
        4. Hybride avec seuils
        """
        
        if scale_factor <= 0:
            return base_width
        
        # Stratégie hybride recommandée
        if scale_factor < 0.5:
            # Très petite échelle : limiter l'épaississement
            return min(base_width / scale_factor, base_width * 4)
        elif scale_factor < 2.0:
            # Échelle normale : inversement proportionnel
            return base_width / scale_factor
        else:
            # Grande échelle : réduction plus douce
            import math
            return base_width / math.sqrt(scale_factor)'''
    
    def find_pipe_elements(self, root: ET.Element) -> List[ET.Element]:
        """Trouve tous les éléments avec ID du type 'Pipexxx'"""
        pipe_elements = []
        
        # Recherche récursive dans tout l'arbre XML
        for element in root.iter():
            element_id = element.get('id', '')
            
            # Vérifier si l'ID correspond au pattern Pipexxx
            if re.match(r'[Pp]ipe\d*', element_id, re.IGNORECASE):
                pipe_elements.append(element)
                print(f"  🔗 Élément pipe trouvé: {element_id} ({element.tag})")
        
        return pipe_elements
    
    def apply_style_to_element(self, element: ET.Element, style: Dict[str, str]):
        """Applique un style à un élément SVG"""
        original_attrs = {}
        
        # Sauvegarder les attributs originaux (pour debug)
        for attr in ['stroke', 'stroke-width', 'fill']:
            if attr in element.attrib:
                original_attrs[attr] = element.attrib[attr]
        
        # Appliquer les nouveaux styles
        for attr, value in style.items():
            if attr in ['stroke', 'stroke-width', 'fill', 'stroke-linecap', 'stroke-linejoin']:
                element.set(attr, value)
        
        print(f"    🎨 Styles appliqués à {element.get('id', 'unknown')}: {style}")
        if original_attrs:
            print(f"      (original: {original_attrs})")
    
    #MAB: méthode intuilisée
    '''def sync_with_polyline_styles(self, polyline_item):
        """Synchronise avec les styles d'une polyligne existante"""
        
        # Extraire les styles de la polyligne
        normal_pen = polyline_item.normal_pen
        selected_pen = polyline_item.selected_pen
        hover_pen = polyline_item.hover_pen
        
        # Convertir en styles SVG
        self.set_pipe_style('normal',
                           stroke=normal_pen.color().name(),
                           **{'stroke-width': str(normal_pen.width())})
        
        self.set_pipe_style('selected', 
                           stroke=selected_pen.color().name(),
                           **{'stroke-width': str(selected_pen.width())})
        
        self.set_pipe_style('hover',
                           stroke=hover_pen.color().name(), 
                           **{'stroke-width': str(hover_pen.width())})
        
        print("🔄 Styles synchronisés avec les polylignes")'''

# Instance globale du gestionnaire
pipe_style_manager = PipeStyleManager()