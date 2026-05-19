#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 15:15:51 2026

@author: frankavontluck
"""
#heat_demand_ts
import pandas as pd
import numpy as np
import parameter as para
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

weather = pd.read_csv(
    "Temperatur Meldorf 2025.csv",
    parse_dates=["date"],
    index_col="date"
)

T_out = weather["tavg"]

# tägliche Frequenz
T_out = T_out.asfreq("D")

#Heizgradform (noch keine Leistung)
heat_shape = (para.T_REF - T_out).clip(lower=0)

#Grundlast hinzufügen
shape_temp = heat_shape / heat_shape.sum()
shape_base = pd.Series(
    np.ones(len(shape_temp)) / len(shape_temp),
    index=shape_temp.index
)

shape_total = (
    (1 - para.BASE_SHARE) * shape_temp
    + para.BASE_SHARE * shape_base
)
shape_total /= shape_total.sum()
shape_total.sum() == 1.0

#auf Jahreswärmemenge skalieren (2025)
#Wärmelast als Energiezeitreihe
heat_energy_ts = shape_total * para.ANNUAL_HEAT_MWH

#Umrechnung in Leistung
dt_hours = (
    heat_energy_ts.index.to_series()
    .diff()
    .dt.total_seconds()
    .fillna(24*3600)
    / 3600
)

heat_demand_ts = heat_energy_ts / dt_hours

type(heat_demand_ts)   # pandas Series
heat_demand_ts.name   # optional

#Interpolation, da nur Wettedaten in 24h Auflösung
heat_demand_ts_hourly = heat_demand_ts.resample("h").interpolate("linear")

#snapshots vorgeben und reindex
snapshots = pd.date_range(
    "2025-01-01 00:00",
    "2025-12-31 23:00",
    freq="h"
)

heat_demand_ts_hourly = (
    heat_demand_ts_hourly
    .tz_localize(None)
    .reindex(snapshots)
    .interpolate("linear")
)


#plot

#heat_demand_ts_hourly.plot(title="Heat Demand (Grosskunden) MW")
#plt.xlabel("Time")
#plt.ylabel("Power [MW]")
#max_val = heat_demand_ts_hourly.max()
#plt.ylim(0, max_val * 1.1)
#plt.show()

def plot_heat_demand(ts):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ts.index, ts.values)
    ax.set_title("Heat Demand (Grosskunden) MW")
    ax.set_xlabel("Time")
    ax.set_ylabel("Power [MW]")
    ax.set_ylim(0, 0.35)
    fig.tight_layout()
    return fig

#Wärmeverlust PTES
loss_per_hour = para.loss_per_year_ptes / 8760
    
#Zeitreihe solar
def create_solar_profile (snapshots,filepath, beta=35, rho=0.2):
    #beta Kollektorneigungswinkel (0 ist horizontal)rho Bodenreflektion
    import pandas as pd
    
    weather = pd.read_csv(filepath, skiprows=17, nrows=8760)

    weather.columns = weather.columns.str.strip()

    assert "time(UTC)" in weather.columns, weather.columns
    
    #weather = pd.read_csv(
    #"tmy_meldorf_2005_2023.csv",
    #skiprows=17
    #)


        #Zeitspalte transformieren (Zeitstempel matchen nicht, da TMY vs 2025)
        #weather["time(UTC)"] = pd.to_datetime(weather["time(UTC)"], utc=True)
        #weather = pd.read_csv("tmy_meldorf_2005_2023.csv", skiprows=17)
    

    weather["time(UTC)"] = pd.to_datetime(
    weather["time(UTC)"],
    format="%Y%m%d:%H%M",
    errors="raise",
    utc=True
    )
    
    weather = weather.set_index("time(UTC)")
    
    #Zeitzone entfernen
    weather.index = weather.index.tz_localize(None)

    weather.index = weather.index.map(lambda t: t.replace(year=2025)) #synthetisches jahr 2025
    
    #Vereinfachte geneigte Strahlung
    
    G_tilt = (weather["Gb(n)"] * np.cos(np.radians(beta)) +
              weather["Gd(h)"] * (1 + np.cos(np.radians(beta))) / 2 +
              weather["G(h)"] * rho * (1 - np.cos(np.radians(beta))) / 2)
    

   
    
    # Auf Snapshots mappen
    #G_tilt = G_tilt.reindex(snapshots).fillna(0)
    G_tilt = G_tilt.reindex(snapshots).interpolate().fillna(0) 
    print("G_tilt max after reindex:", G_tilt.max())
    
    # Normieren für p_max_pu
    #solar_profile = G_tilt / G_tilt.max()
    max_val = G_tilt.max()

    if pd.isna(max_val) or max_val == 0:
        solar_profile = G_tilt * 0
    else:
        solar_profile = G_tilt / max_val
    solar_profile = solar_profile.reindex(snapshots).fillna(0)
   
    
    return solar_profile

#Funktion zur Anwendung des CO2 Preises
def apply_co2_price(n,scenario):
    CO2_PRICE = scenario["CO2_PRICE"]
    
    #Gas links
    gas_links = ["Gas_Brennwert","Gas_Reserve"]
    
    for link in gas_links:
        ef = para.ef_gas
        n.links.loc[link,"marginal_cost"]+=ef*CO2_PRICE
        
    #Biogas BHKW
    biogas_links = ["BHKW_1","BHKW_2"]
    
    for link in biogas_links:
        ef = para.ef_biogas
        n.links.loc[link,"marginal_cost"]+=ef*CO2_PRICE
        
#W#rmeverlust PTES
def calculate_standing_loss(snapshots, annual_loss):
    annual_loss=para.loss_per_year_ptes 
    n_timesteps_per_year = len(snapshots)
    standing_loss_per_snapshot = 1- (1-annual_loss)**(1/n_timesteps_per_year)
    return standing_loss_per_snapshot

#Zeitreihe Strompreis

#Einlesen csv
def load_price_timeseries(path):
    try:
        # Versuch: CSV mit Header
        df = pd.read_csv(
            "electricity_prices_2025.csv",
            sep=";",   #semikolon als Trennzeichen
            decimal=",", #Zahlen haben Komma als Trennzeichen
            parse_dates=["date"],
        )
    except:
        # Fallback: CSV ohne Header
        df = pd.read_csv(
            "electricity_prices_2025.csv",
            sep=";",
            decimal=",",
            header=None,
            names=["date", "price"]
        )
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d %H:%M:%S")
#2. Daten aufräumen
    df = df.dropna()

    # sicherstellen, dass price float ist
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Datum als Index setzen
    df = df.set_index("date")

    # sortieren (wichtig für PyPSA)
    df = df.sort_index()

    #3. Stündliche Zeitreihe
    df = df.resample("h").mean()

    # optional: fehlende Werte interpolieren
    df["price"] = df["price"].interpolate()

    return df


#4. Anwendung
df_prices = load_price_timeseries("electricity_prices_2025.csv")



def load_electricity_price_with_charges(path, para, snapshots):

    df = load_price_timeseries(path)

    #auf Snapshots bringen
    prices = df["price"].reindex(snapshots).interpolate()

   #Preise
    variable_costs = float(
        para.stromsteuer +
        para.netzentgelt_AP +
        para.konzessionsabgabe +
        para.kwk_umlage +
        para.offshore_netzumlage
    )

    total_price = prices + variable_costs

    return total_price


    
        
        
    
    
    
    





























