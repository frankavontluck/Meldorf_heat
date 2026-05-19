#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:19:18 2026

@author: frankavontluck
"""


#optimierung:


def run(n):
    status,condition=n.optimize( #Befehl schauen in docs?
        solver_name="gurobi",
        solver_options={"OutputFlag":1,
                        "LogToConsole":1}

    )
    print("")
    print("--- SOLVER STATUS ---")
    print("status:", status)
    print("condition:", condition)

    
    return n,status,condition


