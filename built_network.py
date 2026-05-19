#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:28:31 2026

@author: frankavontluck
"""
#pysik wird hier gebaut
#alles hinzufügen ohen scenarios logik
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import parameter as para
import functions as func
import plotly.io as pio
import plotly.offline as py
import matplotlib.dates as mdates
import numpy as np


def built_base_network(snapshots, heat_demand_ts):
    n = pypsa.Network()

    n.set_snapshots(snapshots)
    
    #Zeitreihe auf gleiche Snapshots wie Network bringen
    func.heat_demand_ts_hourly = (
        func.heat_demand_ts_hourly
        .tz_localize(None)                 # falls Zeitzone existiert
        .reindex(snapshots)
        .interpolate(method="linear")
    )
#Solarprofil aus functions abrufen
    solar_profile = func.create_solar_profile(
    snapshots, 
    "tmy_meldorf_2005_2023.csv"
)

#Wärmeverlust PTES übergeben
    standing_loss_ptes = func.calculate_standing_loss(snapshots,annual_loss=0.2)
    
#Zeitreihe Biogas
    biogas_df = pd.read_csv(
       "zeitreihe_BHKW_Leistung_komplett.csv",
       sep=";",
       decimal=","
    )

    biogas_df.columns = biogas_df.columns.str.strip().str.lower()

# robust gegen Whitespaces / floats / missing values
    biogas_df["snapshot"] = pd.to_datetime(
        biogas_df["date"].astype(str).str.strip() + " " +
        biogas_df["time"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    )

    biogas_df = biogas_df.dropna(subset=["snapshot"])
    biogas_df = biogas_df.set_index("snapshot")

    biogas_profile = biogas_df["p_fuel [mw]"]

    biogas_profile = biogas_profile.reindex(n.snapshots)
    biogas_profile = biogas_profile.fillna(0)
    biogas_profile = biogas_profile / biogas_profile.max()
    n.biogas_profile = biogas_profile
    
    
#Status quo


# Carrier definieren
    n.add("Carrier", "gas", co2_emissions=para.ef_gas)
    n.add("Carrier", "biogas", co2_emissions=para.ef_biogas)
    n.add("Carrier", "heat")
    n.add("Carrier", "solar_heat", co2_emissions=0)
    n.add("Carrier", "electricity", co2_emissions=para.ef_electricity)
    n.add("Carrier", "heat_pump",co2_emissions=0)
    n.add("Carrier", "biogas_penalty")
    n.add("Carrier", "heat_dump")
    n.add("Carrier", "heat_storage_charge")
    n.add("Carrier", "heat_storage")

#Busses hinzufügen
    n.add("Bus", "gas", carrier="gas") #efficiency ist Hi (heizwert) basiert
    n.add("Bus", "biogas", carrier="biogas") #efficiency ist Hi basiert
    #n.add("Bus", "heat_supply", carrier="heat")
    n.add("Bus", "heat_demand", carrier="heat")
    n.add("Bus", "heat_storage", carrier="heat")
    n.add("Bus", "heat_low", carrier="heat")
    n.add("Bus", "heat_high", carrier="heat")
    n.add("Bus", "electricity", carrier="electricity")
    n.add("Bus","heat_dump", carrier="heat")
    n.add("Bus","biogas_dump", carrier= "biogas")
    
#Gas Brennstoff bereitstellung
    n.add(
        "Generator",
        "gas_supply",
        bus="gas",
        carrier="gas",
        p_nom=1e6,  # quasi unbegrenzt
        marginal_cost=para.cost_gas
        )

#zur zentralen Brennstoffkostenänderung
#Biogas muss fest abgenommen werden daher load
    n.add(
         "Load",
         "biogas_source",
         bus="biogas",
         p_set=0
         )
    n.loads_t.p_set["biogas_source"] = -biogas_profile
    #n.add(
        #"Generator",
        #"biogas_supply",
        #bus="biogas",
        #carrier="biogas",
        #p_nom=1, #quasi unbegrenzt
        #p_max_pu=biogas_profile, #einlesen Zeitreihe
        #p_min_pu=biogas_profile, #must run generator
        #marginal_cost=para.cost_biogas # (€/MWh_hi)
        #)
    #n.generators_t.p_min_pu["biogas_supply"] = biogas_profile
    #n.generators_t.p_max_pu["biogas_supply"] = biogas_profile

    
    
#Hinzufügen 1. Biogas BHKW (Agenitor 306)
    n.add(
        "Link",
        "BHKW_1",
        carrier="biogas",
        bus0="biogas",
        bus1="heat_high",
        #bus2="electricity",      # optional, falls Strom relevant
        efficiency=0.462,          # Wärme
        #efficiency2=0.4,         # Strom
        efficiency2=0,              # for consistency
        p_nom=0.29/0.462,  # MW_th p_nom=th_capacity/eta_th
        #p_min_pu = biogas_profile,
        #p_max_pu = biogas_profile,
        marginal_cost=35.65,         # €/MWh_biogas 
        capital_cost=0           # Bestand
        )

#2. Biogas BHKW (Agenitor 408 BG)
    n.add(
        "Link",
        "BHKW_2",
        carrier="biogas",
        bus0="biogas",
        bus1="heat_high",
        #bus2="electricity",      # optional, falls Strom relevant
        efficiency=0.407,          # Wärme
        #efficiency2=0.4,         # Strom
        efficiency2=0, # for consistency
        p_nom =0.345/0.407,                 # MW_th
        #p_min_pu = biogas_profile,
        #p_max_pu = biogas_profile,
        marginal_cost=39.86,         # €/MWh_biogas (
        capital_cost=0           # Bestand
        )
    
#Biogas dump mit Strafkosten
    n.add(
        "Link",
        "Biogas_NotUsed",
        carrier="biogas_penalty",
        bus0="biogas",
        bus1="biogas_dump",
        efficiency=1.0,
        efficiency2=0,
        p_nom=1,
        p_nom_extendable=True,
        marginal_cost=para.biogas_take_or_pay_cost
        )
#Erdgaskessel (Brennwertkessel Vitocrossal 200 CM2 --> Normalbetrieb)
    n.add(
        "Link",
        "Gas_Brennwert",
        carrier="gas",
        bus0="gas",
        bus1="heat_high",
        efficiency=1.05, #da Breennwertkessel eta_hi kann > 1
        efficiency2=0,
        p_nom=0.62,
        marginal_cost=1.1 #nur variable O&M
        )
#Erdgaskessel (Heizwertkessel Vitoplex --> Nur Notfallbetrieb)
    n.add(
        "Link",
        "Gas_Reserve",
        carrier="gas",
        bus0="gas",
        bus1="heat_high",
        efficiency=0.92,
        efficiency2=0,
        p_nom=1.6,
        marginal_cost=200,       #kpünstlich hoch, nur notfallbetrieb
        p_min_pu=0
        )
#heat dump Biogas status_quo
    n.add(
        "Link",
        "Heat_Dump",
        carrier="heat_dump",
        bus0="heat_high",
        bus1="heat_dump",
        efficiency=1.0,
        p_nom=1,
        p_nom_extendable=True,
        marginal_cost=1000 #€/MWh_th
        )
#Netzstrombezug
    n.add(
        "Generator",
        "grid_import",
        bus="electricity",
        carrier="electricity",
        p_nom=1000,              # quasi unbegrenzt
        p_nom_extendable = True,
        capital_cost=para.netzentgelt_LP,  # €/MW/a
        marginal_cost=0         # WICHTIG: kommt später als Zeitreihe!
        )
    
#1.Ausbaustufe (PTES inkl. Solarthermie und 2 WP)

#Solarthermie zur Befüllung des PTES


    n.add(
        "Generator",
        "Solar_Thermal",
        bus="heat_low",
        carrier="solar_heat",
        p_nom_extendable=True,
        p_max_pu=solar_profile, #Zeitreihenprofil 0-1 
        marginal_cost=0, #keine laufenden Kosten
        capital_cost=23948 #berechnet aus dänischem Technologiekatalog €/MW_th
        )

 

#PTES
    n.add(
        "Store",
        "PTES",
        bus="heat_storage",
        e_nom=870, #Mwh_th #annahme aus sehr geringer temperaturspreizung
        standing_loss=standing_loss_ptes,
        e_cyclic=True #Speicher Jahresanfang = Jahresende
        ) 
    
#PTES laden
    n.add(
        "Link",
        "PTES_charge",
        carrier="heat_storage_charge",
        bus0 ="heat_low",
        bus1 = "heat_storage",
        efficiency=0.98, #Ladeverluste
        efficiency2=0,
        p_nom=0,
        p_nom_extendable = True, #Entladeleistung wird bei Optimierung angepasst
        capital_cost = para.cost_ptes_power_charge,
        marginal_cost=0
        )  

#PTES in transition szenario mit Biogas laden (high_temp)
    n.add(
        "Link",
        "PTES_charge_highT",
        carrier="heat_storage",
        bus0="heat_high",
        bus1="heat_storage",
        efficiency=0.98,
        p_nom=0, #um Überschusswärme aus Biogas einspeisen zu können
        p_nom_extendable=True,
        capital_cost=para.cost_ptes_power_charge_highT,
        marginal_cost=0
        )

    
#PTES in WP entladen
    n.add(
        "Link",
        "PTES_discharge",
        bus0 = "heat_storage",
        bus1 = "heat_low",
        efficiency = 0.98,
        efficiency2=0,
        p_nom=0,
        p_nom_extendable = True,
        capital_cost = para.cost_ptes_power_discharge,
        marginal_cost=0
        )   
    
#WP nach dem PTES (PTES als Wärmequelle, Rücklaufnutzung)
    
#Netzkopplung
    n.add(
        "Link",
        "Übergabestation",
        carrier="heat",
        bus0="heat_high",
        bus1="heat_demand",
        efficiency=0.98,     # Netzverluste
        efficiency2=0,
        p_nom=0,
        p_nom_extendable=True
        )

#Wärmepumpe nach dem PTES 



    n.add(
        "Link",
        "WP_booster",
        carrier="heat_pump",
        bus0="heat_high",
        bus1="heat_low",
        bus2="electricity",
        efficiency=(para.COP_HP-1)/para.COP_HP,
        efficiency2=1/para.COP_HP,
        p_nom=1.2,
        p_min_pu=-1,
        p_max_pu=0,
        p_nom_extendable=False,
        marginal_cost=0
        )
   
    
    #Großkunden hinzufügen
    n.add(
        "Load",
        "Grosskunden",
        bus="heat_demand",
        p_set=heat_demand_ts
        )
    return n








