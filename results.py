#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 10:19:03 2026

@author: frankavontluck
"""
import pandas as pd
import parameter as para

def safe_link_p1_sum(n, link_name):
    if link_name not in n.links_t.p1.columns:
        print("WARNUNG: Link fehlt in n.links_t.p1:", link_name)
        return 0

    return n.links_t.p1[link_name].sum()


def summarize_results(n, scenario_name):
    results = {}
    
    

    #Gesamtkosten des Systems
    results["system_costs"] = n.objective

    #Gasverbrauch (MWh)
    gas_use = 0

    if "Gas_Brennwert" in n.links_t.p0:
            gas_use += n.links_t.p0["Gas_Brennwert"].sum()

    if "Gas_Reserve" in n.links_t.p0:
            gas_use += n.links_t.p0["Gas_Reserve"].sum()

    #Biogasverbrauch
    #biogas_use = n.links_t.p0["BHKW_1"].sum() + n.links_t.p0["BHKW_2"].sum()
    biogas_use = 0

    if "BHKW_1" in n.links_t.p0:
        biogas_use += n.links_t.p0["BHKW_1"].sum()

    if "BHKW_2" in n.links_t.p0:
        biogas_use += n.links_t.p0["BHKW_2"].sum() #robustere version

    #Emissionen berechnen
    emissions_gas = gas_use * para.ef_gas
    emissions_biogas = biogas_use * para.ef_biogas

    results["emissions_total"] = emissions_gas + emissions_biogas
 
    
    #Wärmeerzeugung
    results["gas"] = -(
    safe_link_p1_sum(n, "Gas_Brennwert")
    + safe_link_p1_sum(n, "Gas_Reserve")
    )
    results["biogas"] = -(
    safe_link_p1_sum(n, "BHKW_1")
    + safe_link_p1_sum(n, "BHKW_2")
    )


    #results["gas"] = -n.links_t.p1["Gas_Brennwert"].sum()
    #results["biogas"] = (
        #n.links_t.p1["BHKW_1"].sum() +
        #n.links_t.p1["BHKW_2"].sum()
    #)
    
    #Lade- und Entladeleistung PTES
    #results["PTES_charge_p_nom"] = n.links.p_nom_opt.get["PTES_charge",0]
    results["PTES_discharge_p_nom"] = n.links.p_nom_opt.get("PTES_discharge",0)
    
    #PTES Größe zur Kontrolle
    results["PTES_energy_MWh"] = n.stores.e_nom.get("PTES",0)

    results["heat_hp"] = n.links_t.p1.get("WP_booster", pd.Series()).sum()

    results["heat_solar"] = n.generators_t.p.get("Solar_Thermal", pd.Series()).sum()

    results["scenario"] = scenario_name

    return results

