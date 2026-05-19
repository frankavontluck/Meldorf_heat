#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 15:03:36 2026

@author: frankavontluck
"""
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import parameter as para
import functions as func
import plotly.io as pio
import plotly.offline as py
import matplotlib.dates as mdates
import results as res
import gurobipy as gp
import built_network as built
import analysis


from scenarios import scenarios
from built_network import built_base_network
from apply_scenario import apply_scenario
from run_optimization import run
from results import summarize_results


pd.options.plotting.backend = "plotly"
n = pypsa.Network(name='meldorf')

  #snapshots definieren (jahr:2025)
snapshots = pd.date_range(
   start="2025-01-01 00:00",
   end="2025-12-31 23:00",
   freq="h"
    )


heat_demand_ts = func.heat_demand_ts_hourly


#Original Wärmebedarf Großkunde

#scenario schleife

results_table = []


for name, scenario in scenarios.items(): #loopvariable anders benannt als importvariable
    print(f"Running scenario: {name} ")
    n = built_base_network(snapshots, heat_demand_ts)
    n = apply_scenario(n, scenario)
    
    # --------------------------------------------------
# EX-ANTE BIOGAS-ÜBERSCHUSSANALYSE (status_quo)
# --------------------------------------------------
    if name == "status_quo":

    # Biogas-Profil aus dem Network holen
        biogas_profile = n.biogas_profile

    # BHKW-Parameter direkt aus dem Network
        bhkw_params = [
            {
            "p_nom": n.links.at["BHKW_1", "p_nom"],
            "eta_th": n.links.at["BHKW_1", "efficiency"],
            },
            {
            "p_nom": n.links.at["BHKW_2", "p_nom"],
            "eta_th": n.links.at["BHKW_2", "efficiency"],
            },
            ]

        ex_ante = analysis.analyze_biogas_excess(
            heat_demand_ts=n.loads_t.p_set["Grosskunden"],
            biogas_profile=biogas_profile,
            bhkw_params=bhkw_params,
            scenario_name=name,
            )

        print("")
        print("--- EX-ANTE BIOGAS ÜBERSCHUSS (status_quo) ---")
        print("Szenario:", ex_ante["scenario"])
        print("Überschussstunden:", ex_ante["excess_hours"])
        print("Überschussenergie [MWh]:", ex_ante["excess_energy_MWh"])
        print("Max. Überschussleistung [MW]:", ex_ante["excess_peak_MW"])
        print("Anteil Überschussstunden:", ex_ante["share_excess_hours"])


    
    
    #debug biogas
    #print("\n--- BUS CHECK ---")
    #print("Buses:", n.buses.index)

    #print("\nLinks an heat_high:")
    #print(n.links[(n.links.bus0 == "heat_high") | (n.links.bus1 == "heat_high")])

    #print("\nLoads:")
    #print(n.loads)
    #debug großkunden
   #print("Load max:", n.loads_t.p_set["Grosskunden"].max())
    #print("Übergabestation p_nom:", n.links.loc["Übergabestation","p_nom"])
    #print("Max biogas profile:", n.biogas_profile.max())

    #print("BHKW capacity max:",
     # n.links.loc["BHKW_1","p_nom"] + n.links.loc["BHKW_2","p_nom"])
    #print(n.links.loc["Biogas_NotUsed", ["bus0","bus1","p_nom","p_nom_extendable"]])
    #print("CHECK")
    #print(n.generators.loc["biogas_supply", ["p_min_pu","p_max_pu"]])
    #print(n.generators_t.p_min_pu["biogas_supply"].head())
    #print(n.buses)
    #n.consistency_check()



    #Isolations check
    #n.generators.at["biogas_supply", "p_nom"] = 0
    #biogas debug logik
    print("\n--- BIOGAS LINK CHECK ---")

    print(n.links.loc[["BHKW_1","BHKW_2","Biogas_NotUsed"],
                  ["bus0","bus1","efficiency","p_nom","p_nom_extendable"]])
    print("identisch")
    print(n.loads_t.p_set["biogas_source"].shape)
    print(n.snapshots.shape)
    print("Load zeitreihe")
    print(n.loads_t.p_set["biogas_source"].shape)
    print(n.snapshots.shape)
    print("match timestamp")
    print(n.loads_t.p_set["biogas_source"].isna().sum())
    print("SNAPSHOTS VS TIME SERIES")
    print(n.snapshots[0], n.snapshots[-1])
    print(n.loads_t.p_set.index[0], n.loads_t.p_set.index[-1])
    print("NAN in Zeitreihe")
    print(n.snapshots[0], n.snapshots[-1])
    print(n.loads_t.p_set.index[0], n.loads_t.p_set.index[-1])
    
    print("\n--- FULL NETWORK CHECK ---")
    for bus in ["biogas", "heat_high", "heat_demand"]:
        print(f"\nBUS: {bus}")
    
        print("Incoming links:")
        print(n.links[n.links.bus1 == bus][["bus0","bus1","p_nom"]])
    
        print("Outgoing links:")
        print(n.links[n.links.bus0 == bus][["bus0","bus1","p_nom"]])
    
        print("Generators:")
        print(n.generators[n.generators.bus == bus].index.tolist())
    
        print("Loads:")
        print(n.loads[n.loads.bus == bus].index.tolist())
   
    
    

    #robuster machen
    n, status, condition = run(n)
    
    #debug biogas must-run
    #Biogas debug
    print("\n--- BIOGAS DEBUG ---")

    if "biogas_source" in n.loads_t.p_set.columns:
        print("Biogas eingespeist (Load):",
          n.loads_t.p_set["biogas_source"].sum())

    if "Biogas_NotUsed" in n.links_t.p0.columns:
        print("Biogas_NotUsed:",
          n.links_t.p0["Biogas_NotUsed"].sum())

    bhkw_biogas = 0

    if "BHKW_1" in n.links_t.p0.columns:
        bhkw_biogas += n.links_t.p0["BHKW_1"].sum()

    if "BHKW_2" in n.links_t.p0.columns:
        bhkw_biogas += n.links_t.p0["BHKW_2"].sum()

    print("Biogas über BHKW:", bhkw_biogas)

    print("")
    print("--- DEBUG BIOGAS ---")

    if status == "ok" and condition == "optimal":
        
        if "biogas_source" in n.loads_t.p_set.columns:        
            print("biogas_source sum:",              
                  n.loads_t.p_set["biogas_source"].sum())    
            if "Biogas_NotUsed" in n.links_t.p0.columns:        
                print("Biogas_NotUsed sum:",              
                      n.links_t.p0["Biogas_NotUsed"].sum())
        

        if "biogas_supply" in n.generators_t.p.columns:
            print("biogas_supply sum:")
            print(n.generators_t.p["biogas_supply"].sum())
        else:
            print("biogas_supply hat keinen Dispatch (0 oder nicht genutzt)")

        bhkw_biogas = 0.0

        if "BHKW_1" in n.links_t.p0.columns:
           bhkw_biogas += n.links_t.p0["BHKW_1"].sum()

        if "BHKW_2" in n.links_t.p0.columns:
            bhkw_biogas += n.links_t.p0["BHKW_2"].sum()

        print("Biogas über BHKW umgesetzt (Brennstoff):")
        print(bhkw_biogas)

        if "Biogas_NotUsed" in n.links_t.p0.columns:
            print("Biogas_NotUsed (Penalty):")
            print(n.links_t.p0["Biogas_NotUsed"].sum())
        else:
            print("Biogas_NotUsed nicht genutzt")

    else:
        print("Biogas-Debug übersprungen (keine optimale Lösung)")
    
    #debug PTES
    print(n.stores)
    

    #debug
    print("")
    print("--- DEBUG STROM ---")

    if condition == "optimal" and "grid_import" in n.generators_t.p.columns:
        print("grid_import sum:")
        print(n.generators_t.p["grid_import"].sum())

        print("grid_import min/max:")
        print(
        n.generators_t.p["grid_import"].min(),
        n.generators_t.p["grid_import"].max()
    )
    else:
        print("Strom-Debug übersprungen (keine Lösung oder kein Dispatch)")

    res = summarize_results(n, name)
    results_table.append(res)
    #n = run(n)
#ergebnisse berechnen

    #res = summarize_results(n, name)
    #results_table.append(res)
    
    n.export_to_netcdf(f"results_{name}.nc")
    
    print(f"Finished scenario:{name}")
    
results_df = pd.DataFrame(results_table)
results_df.to_csv("scenario_results.csv", index=False)

print("Solved:", n.objective)
print("Links vorhanden:", n.links.index)
print("Dispatch vorhanden:", n.links_t.p0.columns)
    

    
#Solarprofil
beta_choice = 35 
solar_profile = func.create_solar_profile(
    n.snapshots,
    "tmy_meldorf_2005_2023.csv"
)

    








#plotten des Wärmebedarfs aller Großkunden
#fig = func.plot_heat_demand(func.heat_demand_ts_hourly)
#fig.show()



#skalierbarer Wärmebdarf
demand_ts_scaled=func.heat_demand_ts_hourly*para.scale_factor
























