# =============================================================================
# src/flowcad/gui/graphics/svg_content_handler.py
# =============================================================================
"""
Gestionnaire de contenu SVG - Modifications de texte, valeurs, visibilité
"""

import xml.etree.ElementTree as ET
from typing import Dict, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal


class SVGContentHandler(QObject):
    """
    Gère les modifications de contenu SVG (texte, valeurs, etc.)
    """
    
    # Signal émis quand le contenu change
    content_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        print("✅ SVGContentHandler initialisé")
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def apply_content(self, 
                      root: ET.Element, 
                      content_config: Dict) -> ET.Element:
        """
        Applique des modifications de contenu.
        
        Args:
            root: Élément racine du SVG
            content_config: {
                'text_elements': {
                    'Name': 'B',
                    'label_debit': '150 L/h'
                },
                'visibility': {
                    'optional_element': True
                }
            }
        
        Returns:
            Élément racine modifié
        """
        
        # Modifier les éléments texte
        if 'text_elements' in content_config:
            root = self._modify_text_elements(root, content_config['text_elements'])
        
        # Modifier la visibilité (futur)
        if 'visibility' in content_config:
            root = self._modify_visibility(root, content_config['visibility'])
        
        return root
    
    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================
    
    def _modify_text_elements(self, 
                              root: ET.Element, 
                              text_mods: Dict[str, str]) -> ET.Element:
        """
        Modifie les éléments <text> par ID.
        
        Args:
            root: Élément racine du SVG
            text_mods: {'element_id': 'nouveau_texte'}
        """
        for element_id, new_text in text_mods.items():
            # Chercher l'élément par ID
            text_element = self._find_element_by_id(root, element_id)
            
            if text_element is not None:
                # Vérifier que c'est bien un élément <text>
                if text_element.tag.endswith('text'):
                    # Modifier le texte (dans le premier <tspan> ou directement)
                    self._set_text_content(text_element, new_text)
                    print(f"✏️ Texte '{element_id}' modifié: '{new_text}'")
                else:
                    print(f"⚠️ Élément '{element_id}' trouvé mais ce n'est pas un <text>")
            else:
                print(f"⚠️ Élément texte '{element_id}' non trouvé dans le SVG")
        
        return root
    
    def _find_element_by_id(self, 
                           root: ET.Element, 
                           element_id: str) -> Optional[ET.Element]:
        """Trouve un élément par son ID"""
        # Recherche récursive
        for element in root.iter():
            if element.get('id') == element_id:
                return element
        return None
    
    def _set_text_content(self, text_element: ET.Element, new_text: str):
        """
        Définit le contenu texte d'un élément <text>.
        Gère les cas avec ou sans <tspan>.
        """
        # Chercher un <tspan> enfant (cas Inkscape)
        tspan = None
        for child in text_element:
            if child.tag.endswith('tspan'):
                tspan = child
                break
        
        if tspan is not None:
            # Modifier le texte dans le <tspan>
            tspan.text = new_text
            print(f"   → Modifié via <tspan>")
        else:
            # Pas de <tspan>, modifier directement
            text_element.text = new_text
            print(f"   → Modifié directement")
    
    def _modify_visibility(self, 
                          root: ET.Element, 
                          visibility_mods: Dict[str, bool]) -> ET.Element:
        """
        Modifie la visibilité d'éléments.
        
        Args:
            visibility_mods: {'element_id': True/False}
        """
        for element_id, is_visible in visibility_mods.items():
            element = self._find_element_by_id(root, element_id)
            
            if element is not None:
                if is_visible:
                    # Rendre visible
                    element.set('display', 'inline')
                    element.set('opacity', '1.0')
                else:
                    # Cacher
                    element.set('display', 'none')
                
                print(f"👁️ Visibilité '{element_id}': {is_visible}")
        
        return root


# Instance globale
svg_content_handler = SVGContentHandler()