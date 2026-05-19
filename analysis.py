#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 12 14:58:23 2026

@author: frankavontluck
"""
import pandas as pd


def analyze_biogas_excess(
    heat_demand_ts,
    biogas_profile,
    bhkw_params,
    scenario_name=None,
):
    """
    Ex-ante Analyse des Biogas-Wärmeüberschusses.
    Unabhängig von PyPSA-Optimierung.

    Parameters
    ----------
    heat_demand_ts : pd.Series
        Wärmelast [MW_th], stündlich
    biogas_profile : pd.Series
        normierte Biogas-Zeitreihe [0..1]
    bhkw_params : list of dict
        z.B.:
        {
            "p_nom": MW_fuel,
            "eta_th": -
        }
    scenario_name : str, optional
        Nur für Logging / Ausgabe

    Returns
    -------
    dict
    """

    # -----------------------------
    # 1. Biogas-Wärmeerzeugung
    # -----------------------------
    heat_biogas_ts = pd.Series(
        0.0,
        index=heat_demand_ts.index,
        name="biogas_heat"
    )

    for bhkw in bhkw_params:
        heat_biogas_ts += (
            biogas_profile
            * bhkw["p_nom"]
            * bhkw["eta_th"]
        )

    # -----------------------------
    # 2. Überschuss
    # -----------------------------
    excess_heat_ts = (heat_biogas_ts - heat_demand_ts).clip(lower=0)
    excess_heat_ts.name = "excess_heat"

    # -----------------------------
    # 3. Kennzahlen
    # -----------------------------
    results = {
        "scenario": scenario_name,
        "excess_hours": int((excess_heat_ts > 0).sum()),
        "excess_energy_MWh": float(excess_heat_ts.sum()),
        "excess_peak_MW": float(excess_heat_ts.max()),
        "share_excess_hours": float((excess_heat_ts > 0).mean()),
        # Zeitreihen für Debug / Plot
        "heat_biogas_ts": heat_biogas_ts,
        "excess_heat_ts": excess_heat_ts,
    }

    return results
