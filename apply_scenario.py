#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:06:34 2026

@author: frankavontluck
"""
#apply scenario
import functions as func
import parameter as para
import pandas as pd
def apply_scenario(n, scenario):
    func.apply_co2_price(n, scenario)
    
    

    #Wärmebedarf
    n.loads_t.p_set["Grosskunden"] *= scenario["heat_scale"]

    #GAS
    if not scenario["enable_gas"]:
        n.links.loc[
            n.links.carrier == "gas", "p_nom"
        ] = 0
        if "gas_supply" in n.generators.index:
            n.generators.loc["gas_supply", "p_nom"] = 0
        
    #Biogas als load
    if not scenario["enable_biogas"]:
        n.loads_t.p_set["biogas_source"] = 0
    # Biogas als generator
    #if scenario["enable_biogas"]:
        #if "biogas_supply" in n.generators.index:
         
             #n.generators_t.p_max_pu["biogas_supply"] = n.biogas_profile

    #else:
   
        #if "biogas_supply" in n.generators.index:
            #n.generators.at["biogas_supply", "p_nom"] = 0

        #n.links.loc[n.links.carrier == "biogas", "p_nom"] = 0

           


    
    #PTES
    if not scenario["enable_ptes"]:
        # Store bleibt, aber ohne nutzbare Kapazität
        n.stores.at["PTES", "e_nom"] = 1e-6
        n.stores.at["PTES", "e_cyclic"] = False

    # Alle PTES-Leistungslinks vollständig sperren
    #for link in ["PTES_charge", "PTES_charge_highT", "PTES_discharge"]:
        #if link in n.links.index:
            #n.links.at[link, "active"] = False
        for link in ["PTES_charge", "PTES_charge_highT", "PTES_discharge"]:
            if link in n.links.index:
                n.links.at[link, "p_nom"] = 0
                n.links.at[link, "p_nom_extendable"] = False
        

             
    #Strompreis für Wärmepumpe

    if not scenario["enable_hp"]:
        n.links.at["WP_booster", "p_nom"] = 0
        n.links.at["WP_booster", "p_min_pu"] = 0   
        n.links.at["WP_booster", "p_max_pu"] = 0   
    else:
        #1.endkundenpreis aus functions laden
        total_price = func.load_electricity_price_with_charges(
            scenario["price_file"],
            para,
            n.snapshots
        )
        n.generators_t.marginal_cost.loc[:, "grid_import"] = total_price

        # 2. marginal cost Wärmepumpe (Zeitreihe)
        #hp_marginal_cost = total_price / para.COP_HP + para.C_VAR_OM_HP
        
    #3. alternativer Weg
       # n.links_t.marginal_cost.loc[:, "WP_booster"] = hp_marginal_cost

    # 3. DataFrame sicherstellen (testen ob jetzt der strompreis eingelesen wird)
       # if "marginal_cost" not in n.links_t:
          #  n.links_t["marginal_cost"] = pd.DataFrame(
              #  index=n.snapshots,
               # columns=n.links.index
               # )
            
    # 4. setzen
      #  n.links_t["marginal_cost"]["WP_booster"] = hp_marginal_cost

 
        
    #Solar 
    if not scenario["enable_solar"]:
        print("Solar wird deaktiviert in Szenario:", scenario)
        n.generators_t.p_max_pu.loc[:, "Solar_Thermal"] = 0
        
    # Sicherstellen, dass Dump IMMER verfügbar ist (Debug/Test)
    #if "Heat_Dump" in n.links.index:
        #n.links.at["Heat_Dump", "p_nom"] = 10
       # n.links.at["Heat_Dump", "p_nom_extendable"] = False
    #biogas not used immer iwo hin
    #n.links.at["Biogas_NotUsed", "p_nom"] = 10
    #n.links.at["Biogas_NotUsed", "p_nom_extendable"] = False
    
    # harte Senken für Presolve stabilität
    #n.links.at["Heat_Dump", "p_nom"] = 1
    #n.links.at["Biogas_NotUsed", "p_nom"] = 1

    return n
