from typing import Dict, List
from ..models.equipment.network_equipment import NetworkEquipment
from ..gui.graphics.polyline_graphics import PolylineGraphicsItem
from ..gui.graphics.equipment_graphics import EquipmentGraphicsItem
from .equipment_factory import EquipmentFactory
from .pipe_factory import PipeFactory

class NetworkBuilder:
    """Construit un réseau métier depuis les éléments GUI"""
    
    @staticmethod
    def build_from_canvas(drawing_canvas) -> NetworkEquipment:
        """
        Construit un NetworkEquipment depuis le contenu du canvas
        
        Args:
            drawing_canvas: Instance de DrawingCanvas
            
        Returns:
            NetworkEquipment prêt pour simulation
        """
        network = NetworkEquipment("canvas_network")
        
        # 1. Créer tous les équipements métier
        NetworkBuilder._add_equipments_to_network(network, drawing_canvas)

        # 2. Connecter les equipements entre eux
        NetworkBuilder._connect_equipments(network, drawing_canvas)
        
        return network
    
    @staticmethod
    def _add_equipments_to_network(network: NetworkEquipment, canvas):
        """Ajoute tous les équipements GUI au réseau métier"""
        
        gui_equipments = canvas.get_all_equipment()  # Dict[str, EquipmentGraphicsItem]
        
        # Parcourir et créer les équipements métier
        for gui_id, gui_item in gui_equipments.items():
            try:
                # Créer l'équipement métier via la factory
                business_equipment = EquipmentFactory.create_from_gui_item(gui_item)
                print(f"Création équipement {gui_id} de type {type(business_equipment).__name__}")
                network.add_equipment(business_equipment)
                print(f"✅ Équipement métier créé: {gui_id}")
            except Exception as e:
                raise RuntimeError(f"Erreur création équipement {gui_id}: {e}")

        #parcourir et créer les polylignes métier
        gui_polylines = canvas.get_all_polylines()  # Dict[str, PolylineGraphicsItem]
        for gui_id, gui_item in gui_polylines.items():
            try:
                # Créer la polyligne métier via la factory
                business_polyline = PipeFactory.create_from_gui_polyline(gui_item)
                print(f"Création polyligne {gui_id} de type {type(business_polyline).__name__}")
                network.add_equipment(business_polyline)
                print(f"✅ Polyligne métier créée: {gui_id}")
            except Exception as e:
                raise RuntimeError(f"Erreur création tuyau {gui_id}: {e}")
            

    @staticmethod
    def _connect_equipments(network: NetworkEquipment, canvas):
        """Connecte les équipements entre eux selon les connexions GUI"""
        # À implémenter: parcourir les connexions GUI et relier les équipements métier

        #on parcoure les plylines pour connecter les équipements
        gui_polylines = canvas.get_all_polylines()  # Dict[str, PolylineGraphicsItem]
        for gui_id, gui_item in gui_polylines.items():
            start_port = gui_item.start_port  # EquipmentGraphicsItem
            end_port = gui_item.end_port      # EquipmentGraphicsItem
            
            
            start_equipment_id = start_port.parent_equipment.equipment_id
            start_port_id = start_port.port_id
            end_equipment_id = end_port.parent_equipment.equipment_id
            end_port_id = end_port.port_id
            print(f"Connexion tuyau {gui_id} entre {start_equipment_id}, port {start_port_id} et {end_equipment_id}, port {end_port_id}")
            #le tuyau est le premier équipement
            equipment1 = network.get_equipment_by_id(gui_id)

            #l'équipement 2 est celui connecté au start_port
            equipment2 = network.get_equipment_by_id(start_equipment_id)

            #l'équipement 3 est celui connecté au end_port
            equipment3 = network.get_equipment_by_id(end_equipment_id)

            #La première connexion est celle du tuyau start
            #par défaut, on connecte le port P1 du tuyau au start_port de l'équipement 2
            #le start_port du tuyau est toujours P1
            equipment1_port1_ID = f"{equipment1.id}_P1"
            
            #pour l'équipement 2, on cherche le port via son id
            equipment2_port_ID = f"{equipment2.id}_{start_port_id}"
            print(f"Première connexion: ID de l'équipement 1 {equipment1.id} et port de l'équipement 1: {equipment1_port1_ID}  equipement 2: {equipment2.id} et port: {equipment2_port_ID}")

            network.connectEquipments(equipment1, equipment1.ports[equipment1_port1_ID], equipment2, equipment2.ports[equipment2_port_ID])

            #la deuxiomen connextion est cellue du tuyau end
            #par défaut, on connecte le port P2 du tuyau au end_port de l'équipement 3
            #le end_port du tuyau est toujours P2
            equipment1_port2_ID = f"{equipment1.id}_P2"
            

            ##pour l'équipement 3, on cherche le port via son id
            equipment3_port_ID = f"{equipment3.id}_{end_port_id}"
            print(f"Deuxième connexion: ID de l'équipement 1 {equipment1.id} et port de l'équipement 1: {equipment1_port2_ID}  equipement 3: {equipment3.id} et port: {equipment3_port_ID}")

            network.connectEquipments(equipment1, equipment1.ports[equipment1_port2_ID], equipment3, equipment3.ports[equipment3_port_ID])