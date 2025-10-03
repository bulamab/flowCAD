# =============================================================================
# src/flowcad/gui/graphics/svg_dynamic_manager.py
# =============================================================================
"""
Gestionnaire dynamique SVG - Interface unifiée pour modifications SVG
Phase 1 : Façade minimale déléguant à svg_style_handler
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QByteArray

from .svg_style_handler import svg_style_handler
from .svg_content_handler import SVGContentHandler


class SVGDynamicManager(QObject):
    """
    Gestionnaire central pour toutes les modifications SVG.
    
    Phase 1 : Façade minimale pour les styles uniquement
    Phase 2 : Ajout de content_handler et geometry_handler
    """
    
    # Signal émis quand un SVG est modifié
    svg_modified = pyqtSignal(str, str)  # (equipment_id, svg_content)
    
    def __init__(self):
        super().__init__()
        
        # Gestionnaires de modifications
        self.style_handler = svg_style_handler
        self.content_handler = SVGContentHandler()
        
        # Cache des SVG modifiés
        self.svg_cache: Dict[str, str] = {}
        
        # Connecter aux changements de styles
        self.style_handler.styles_changed.connect(self._on_styles_changed)
        self.content_handler.content_changed.connect(self._on_content_changed)
        
        print("✅ SVGDynamicManager initialisé")
    
    # =========================================================================
    # API PUBLIQUE - Point d'entrée unique
    # =========================================================================
    
    def modify_svg(self,
                   svg_path: str,
                   equipment_id: str,
                   modifications: Dict[str, Any]) -> Optional[str]:
        """
        Point d'entrée unique pour modifier un SVG.
        
        Args:
            svg_path: Chemin du fichier SVG source
            equipment_id: ID de l'équipement
            modifications: {
                'styles': {
                    'pipe_state': 'normal|selected|hover',
                    'scale_factor': 2.0
                },
                # 🔜 Phase 2:
                # 'content': {...},
                # 'geometry': {...}
            }
        
        Returns:
            Contenu SVG modifié, ou None en cas d'erreur
        """
        # Générer une clé de cache
        cache_key = self._generate_cache_key(svg_path, modifications)
        
        # Vérifier le cache
        if cache_key in self.svg_cache:
            print(f"📦 Cache hit pour {equipment_id}")
            return self.svg_cache[cache_key]
        
        try:
            # Charger le SVG
            svg_content = self._load_svg(svg_path)
            if not svg_content:
                return None
            
            # Parser le XML
            root = ET.fromstring(svg_content)
            
            
            
            # Appliquer les modifications du contenu (texte, images, visibilités)
            if 'content' in modifications:
                root = self.content_handler.apply_content(root, modifications['content'])
            # Appliquer les modifications de style
            if 'styles' in modifications:
                root = self.style_handler.apply_styles(
                    root, 
                    modifications['styles']
                )

            #if 'geometry' in modifications:
            #    root = self.geometry_handler.apply(root, modifications['geometry'])

            # Convertir en string
            modified_svg = ET.tostring(root, encoding='unicode')
            
            # Mettre en cache
            self.svg_cache[cache_key] = modified_svg
            
            # Émettre le signal
            self.svg_modified.emit(equipment_id, modified_svg)
            
            print(f"✅ SVG modifié pour {equipment_id}")
            return modified_svg
            
        except Exception as e:
            print(f"❌ Erreur modification SVG pour {equipment_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clear_cache(self):
        """Vide le cache des SVG modifiés"""
        self.svg_cache.clear()
        print("🗑️ Cache SVG vidé")
    
    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================
    
    def _load_svg(self, svg_path: str) -> Optional[str]:
        """Charge le contenu d'un fichier SVG"""
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Fichier SVG non trouvé: {svg_path}")
            return None
        except Exception as e:
            print(f"❌ Erreur lecture SVG {svg_path}: {e}")
            return None
    
    def _generate_cache_key(self, 
                           svg_path: str, 
                           modifications: Dict) -> str:
        """Génère une clé de cache unique"""
        import hashlib
        import json
        
        # Créer une string représentant l'état complet
        key_data = f"{svg_path}:{json.dumps(modifications, sort_keys=True)}"
        
        # Hash MD5 pour clé courte
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _on_styles_changed(self):
        """Callback quand les styles globaux changent"""
        print("🎨 Styles globaux modifiés - vidage du cache")
        self.clear_cache()
        # Note: Les équipements devront se rafraîchir eux-mêmes

    def _on_content_changed(self):
        """Callback quand le contenu global change"""
        print("📝 Contenu global modifié - vidage du cache")
        self.clear_cache()


# Instance globale
svg_dynamic_manager = SVGDynamicManager()