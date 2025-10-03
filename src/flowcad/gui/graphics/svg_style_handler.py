# =============================================================================
# src/flowcad/gui/graphics/svg_style_handler.py
# =============================================================================
"""
Gestionnaire de styles SVG - Migration progressive depuis pipe_style_manager
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal

# Import de l'ancien manager pour compatibilité temporaire
from .pipe_style_manager import pipe_style_manager


class SVGStyleHandler(QObject):
    """
    Gestionnaire de styles pour les éléments SVG.
    Phase 1 : Wrapper autour de pipe_style_manager
    Phase 2 : Implémentation indépendante
    """
    
    # Signal émis quand les styles changent
    styles_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # ✅ Phase 1 : Déléguer à pipe_style_manager
        self._legacy_manager = pipe_style_manager
        
        # Se connecter aux changements de l'ancien manager
        self._legacy_manager.styles_changed.connect(self.styles_changed.emit)
        
        print("✅ SVGStyleHandler initialisé (mode compatibilité)")
    
    # =========================================================================
    # API PUBLIQUE - Interface moderne
    # =========================================================================
    
    def apply_styles(self, 
                     root: ET.Element, 
                     style_config: Dict) -> ET.Element:
        """
        Point d'entrée principal pour appliquer des styles.
        
        Args:
            root: Élément racine du SVG
            style_config: {
                'pipe_state': 'normal|selected|hover',  # État visuel
                'scale_factor': 2.0,                     # Facteur d'échelle
                'custom_elements': {...}                 # Futur: styles custom
            }
        
        Returns:
            Élément racine modifié
        """
        # ✅ Phase 1 : Déléguer à l'ancien système
        if 'pipe_state' in style_config:
            pipe_state = style_config['pipe_state']
            scale_factor = style_config.get('scale_factor', 1.0)
            
            root = self._apply_pipe_styles_legacy(
                root, 
                pipe_state, 
                scale_factor
            )
        
        # 🔜 Phase 2 : Gérer d'autres types de styles ici
        # if 'custom_elements' in style_config:
        #     root = self._apply_custom_styles(root, style_config['custom_elements'])
        
        return root
    
    def get_pipe_style(self, state: str = 'normal') -> Dict[str, str]:
        """
        Retourne le style des tuyaux pour un état donné.
        
        Args:
            state: 'normal', 'selected', ou 'hover'
        
        Returns:
            Dictionnaire de style SVG
        """
        # ✅ Phase 1 : Déléguer
        return self._legacy_manager.get_pipe_style(state)
    
    def get_scaled_pipe_style(self, 
                              state: str = 'normal', 
                              scale_factor: float = 1.0) -> Dict[str, str]:
        """
        Retourne le style des tuyaux avec ajustement d'échelle.
        
        Args:
            state: 'normal', 'selected', ou 'hover'
            scale_factor: Facteur d'échelle de l'équipement
        
        Returns:
            Dictionnaire de style avec stroke-width ajusté
        """
        # ✅ Phase 1 : Déléguer
        return self._legacy_manager.get_scaled_pipe_style(state, scale_factor)
    
    def set_pipe_style(self, state: str, **style_attrs):
        """
        Modifie le style des tuyaux pour un état donné.
        
        Args:
            state: 'normal', 'selected', ou 'hover'
            **style_attrs: Attributs de style à modifier
        """
        # ✅ Phase 1 : Déléguer
        self._legacy_manager.set_pipe_style(state, **style_attrs)
    
    # =========================================================================
    # MÉTHODES PRIVÉES - Compatibilité Phase 1
    # =========================================================================
    
    def _apply_pipe_styles_legacy(self, 
                                   root: ET.Element, 
                                   state: str, 
                                   scale_factor: float) -> ET.Element:
        """
        Applique les styles de pipes via l'ancien système.
        
        Cette méthode sera remplacée en Phase 2.
        """
        # Obtenir les styles ajustés
        pipe_style = self.get_scaled_pipe_style(state, scale_factor)
        
        # Rechercher tous les éléments Pipexxx
        pipe_elements = self._find_pipe_elements(root)
        
        print(f"🔍 Trouvé {len(pipe_elements)} éléments Pipe (échelle: {scale_factor:.3f})")
        
        # Appliquer les styles
        for element in pipe_elements:
            self._apply_style_to_element(element, pipe_style)
        
        return root
    
    def _find_pipe_elements(self, root: ET.Element) -> list:
        """Trouve tous les éléments avec ID du type 'Pipexxx'"""
        pipe_elements = []
        
        for element in root.iter():
            element_id = element.get('id', '')
            
            # Pattern: Pipe suivi de chiffres/lettres (optionnel)
            if re.match(r'[Pp]ipe\d*', element_id, re.IGNORECASE):
                pipe_elements.append(element)
                print(f"  🔗 Élément pipe trouvé: {element_id} ({element.tag})")
        
        return pipe_elements
    
    def _apply_style_to_element(self, 
                                element: ET.Element, 
                                style: Dict[str, str]):
        """Applique un style à un élément SVG"""
        original_attrs = {}
        
        # Sauvegarder les attributs originaux (pour debug)
        for attr in ['stroke', 'stroke-width', 'fill']:
            if attr in element.attrib:
                original_attrs[attr] = element.attrib[attr]
        
        # Appliquer les nouveaux styles
        for attr, value in style.items():
            if attr in ['stroke', 'stroke-width', 'fill', 
                       'stroke-linecap', 'stroke-linejoin']:
                element.set(attr, value)
        
        if original_attrs:
            print(f"    🎨 Styles appliqués (original: {original_attrs})")
    
    # =========================================================================
    # COMPATIBILITÉ TEMPORAIRE - À supprimer en Phase 3
    # =========================================================================
    
    @property
    def pipe_styles(self):
        """Accès aux styles de l'ancien manager (compatibilité)"""
        return self._legacy_manager.pipe_styles
    
    @property
    def modified_svg_cache(self):
        """Accès au cache de l'ancien manager (compatibilité)"""
        return self._legacy_manager.modified_svg_cache


# Instance globale (comme pipe_style_manager)
svg_style_handler = SVGStyleHandler()