#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 15:11:59 2026

@author: frankavontluck
"""

T_REF = 15.0  # °C
BASE_SHARE = 0.15
ANNUAL_HEAT_MWH = 965.85  # <-- DEIN Wert
#cost_biogas = 30 #Marktpreis/Vollkosten Biogas
cost_gas = 48.07 #Quelle bundesnetzagentur wert 14.05.2026
scale_factor=1 #skalierung des Wärmebedarfs
loss_per_year_ptes=0.2 #Wärmeverlust PTES

#Emissionspreise
BASELINE_EMISSIONS=662.79 #tCO2 pro jahr
CO2_CAP_TRANSITION=0.6*BASELINE_EMISSIONS #beispielsweise
CO2_CAP_RENEWABLE=0.1*BASELINE_EMISSIONS #emissionen nahe null als ziel

#Kosten PTES LAden und Entladen
cost_ptes_power_charge = 130000   # €/MW 
cost_ptes_power_discharge = 130000
cost_ptes_power_charge_highT = 130000 #€/MW
    

#EMISSIONSFAKTOREN
ef_gas=0.201 #tCO2/MWh_hi
ef_biogas=0.152 #tCO2/MWh_hi
ef_solar=0 #tCO2/MWh_th
ef_electricity=0.363 #tCO2/MWh

#Rotationswärmepumpe
COP_HP=4.7 #Basis COP
C_VAR_OM_HP=2.8349 #berechnet auf Basis von Hochtemperatuzr Wärmepumpen #euro/MWh

#Zusatzkosten Strompreis (alles in €/MWh)
stromsteuer=20.5
konzessionsabgabe=1.11
offshore_netzumlage=9.41
kwk_umlage=4.46
netzentgelt_AP=39.8
netzentgelt_LP=153150 #euro/MW 

#strafzahlung Biogas nicht abnahme
biogas_take_or_pay_cost=1000








#Solarthermie als link
#maximale Nennleistung
#p_max_pu=p_max_pu = Q_th/p_nom #normierter Faktor zwischen 0 und 1 #p_nom = Q_th.max()
#Q_th 
#q_nom
#solar_profile


#PTES Store und Lade/Entlade links
#loss #hier Caspar nochmal fragen
#seasonal_standing_loss #dafür Verlust Faktoren erfragen
#E_seasonal #MWH #verschiebbare Wärmemenge des Speichers zwischen Sommer und WInter
#Größe PTES m^3
#store_vol=45000
#VL Temp

#Wärmepumpe rotation als link
#COP_t
#HP_nom


#Netzbetrieb
#p_discharge
#netztemperaur
#VL_temp_netz
#Rohrgröße
#rohr_diam

