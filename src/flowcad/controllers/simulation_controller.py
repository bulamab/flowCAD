from typing import Dict, List, Optional
from ..models.equipment.network_equipment import NetworkEquipment
from ..simulation.simulation_manager import SimulationManager
from .network_builder import NetworkBuilder

class SimulationController:
    """Contrôleur principal pour la simulation"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.drawing_canvas = main_window.drawing_canvas
        self.right_panel = main_window.Right_panel


    #==========================================================================
    #-------------------simulation complète du réseau métier-------------------
    ################################################################################

    def run_complete_simulation(self) -> bool:
        print(f"Simulation en cours")

        #1===========================================================
        #---------------------validation du réseau GUI--------------
        #A faire...

        #2============================================================
        #--------------construction du réseau métier depuis le canvas-
        
        network = NetworkBuilder.build_from_canvas(self.drawing_canvas)

        print(f"Réseau métier construit avec {len(network.equipments)} équipements")
        print(network)


        #3==========================================================================
        #-------------------validation du réseau métier-----------------------------

        
        #4==========================================================================
        #-------------------simulation du réseau métier-----------------------------
        sim_manager = SimulationManager(network)

        results = sim_manager.run_simulation()
        print("Simulation terminée avec succès")
        #print(f"Résultats: {results.node['pressure']}")

        #5==========================================================================
        #-------------------transfer des résultats vers GUI---------------------------
        self.update_gui_with_results(network)

        #6==========================================================================
        #-------------------affichage des résultats sur GUI---------------------------

        return True
    

    def update_gui_with_results(self, business_network: NetworkEquipment):
        """Met à jour la GUI avec les résultats de simulation"""

        for gui_id, business_eq in business_network.equipments.items():
            #print(f"Traitement résultats pour équipement métier {business_eq} de type {type(business_eq).__name__}")
            gui_id = business_eq.id  # Même ID que l'équipement GUI
            print(f"Transfert résultats pour {gui_id}")
            
            # Récupérer l'équipement GUI correspondant  
            gui_item = self.drawing_canvas.get_equipment(gui_id)
            pipe_item = self.drawing_canvas.get_pipe(gui_id)    

            # Extraire les résultats de l'équipement métier
            results = self._extract_results_from_business_equipment(business_eq)

            if gui_item:
                # Mettre à jour les résultats dans la définition GUI
                gui_item.equipment_def['results'].update(results)
                print(f"📊 Résultats transférés pour {gui_id}: {results}")
            elif pipe_item:
                pipe_item.pipe_def['results'].update(results)
                print(f"📊 Résultats transférés pour {gui_id} (polyligne): {results}")
    
    def _extract_results_from_business_equipment(self, business_eq) -> Dict:
        """Extrait les résultats d'un équipement métier"""
        results = {}
        
        # Résultats communs pour tous les types
        if hasattr(business_eq, 'flowrate') and business_eq.flowrate is not None:
            results['flow_rate'] = business_eq.flowrate
        
        # Résultats spécifiques selon le type
        if hasattr(business_eq, 'headloss') and business_eq.headloss is not None:
            results['headloss'] = business_eq.headloss
            
        if hasattr(business_eq, 'velocity') and business_eq.velocity is not None:
            results['velocity'] = business_eq.velocity

        if hasattr(business_eq, 'pressure_1') and business_eq.pressure_1 is not None:
            results['pressure_1'] = business_eq.pressure_1

        if hasattr(business_eq, 'head_1') and business_eq.head_1 is not None:
            results['head_1'] = business_eq.head_1

        if hasattr(business_eq, 'pressure_2') and business_eq.pressure_2 is not None:
            results['pressure_2'] = business_eq.pressure_2

        if hasattr(business_eq, 'head_2') and business_eq.head_2 is not None:
            results['head_2'] = business_eq.head_2

        if hasattr(business_eq, 'pressure_3') and business_eq.pressure_3 is not None:
            results['pressure_3'] = business_eq.pressure_3

        if hasattr(business_eq, 'head_3') and business_eq.head_3 is not None:
            results['head_3'] = business_eq.head_3

        if hasattr(business_eq, 'total_headloss') and business_eq.total_headloss is not None:
            results['total_headloss'] = business_eq.total_headloss

        if hasattr(business_eq, 'head_gain') and business_eq.head_gain is not None:
            results['head_gain'] = business_eq.head_gain

        return results
    
    def _refresh_properties_panel(self):
        """Rafraîchit le panneau des propriétés si un équipement est sélectionné"""
        selected_items = self.drawing_canvas.scene.selectedItems()
        
        # Si un équipement est sélectionné, rafraîchir ses propriétés
        for item in selected_items:
            if hasattr(item, 'equipment_def'):
                self.right_panel.display_properties(item.equipment_def, "equipment")
                break

        