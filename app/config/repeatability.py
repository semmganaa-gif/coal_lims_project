# app/config/repeatability.py
# -*- coding: utf-8 -*-
from math import inf

# Repeatability (T) limits per analysis code (shared by backend & frontend).
# Жишээ (Cl): GB/T 3558-2014 – <150 μg/г үед T=15 μg/г, ≥150 μg/г үед T=10% (percent mode).
LIMIT_RULES = {
    "MT":   {"bands": [{"upper": 10.0, "limit": 0.50, "mode": "abs"},
                       {"upper": inf,  "limit": 0.50, "mode": "percent"}]},
    "Mad":  {"bands": [{"upper": 10.0, "limit": 0.20, "mode": "abs"},
                       {"upper": inf,  "limit": 0.40, "mode": "abs"}],
             "bands_detailed": [
                 {"upper": 0.50, "limit": 0.20, "mode": "abs"},
                 {"upper": 5.00, "limit": 0.20, "mode": "abs"},
                 {"upper": 10.0, "limit": 0.30, "mode": "abs"},
                 {"upper": inf,  "limit": 0.40, "mode": "abs"},
             ]},
    "Vad":  {"bands": [{"upper": 20.0, "limit": 0.30, "mode": "abs"},
                       {"upper": 40.0, "limit": 0.50, "mode": "abs"},
                       {"upper": inf,  "limit": 0.80, "mode": "abs"}]},
    "Aad":  {"bands": [{"upper": 15.0, "limit": 0.20, "mode": "abs"},
                       {"upper": 30.0, "limit": 0.30, "mode": "abs"},
                       {"upper": inf,  "limit": 0.50, "mode": "abs"}]},
    "Gi":   {"bands": [{"upper": 18.0, "limit": 1.0, "mode": "abs"},
                       {"upper": inf,  "limit": 3.0, "mode": "abs"}]},
    "CSN":  {"single": {"limit": 0.60, "mode": "abs"}},
    "CRI":  {"single": {"limit": 2.2, "mode": "abs"}},
    "CSR":  {"single": {"limit": 2.5, "mode": "abs"}},
    "TS":   {"bands": [{"upper": 2.0, "limit": 0.05, "mode": "abs"},
                       {"upper": 5.0, "limit": 0.10, "mode": "abs"},
                       {"upper": inf, "limit": 0.15, "mode": "abs"}]},
    "St,ad": {"bands": [{"upper": 2.0, "limit": 0.05, "mode": "abs"},
                        {"upper": 5.0, "limit": 0.10, "mode": "abs"},
                        {"upper": inf, "limit": 0.15, "mode": "abs"}]},
    "P":    {"bands": [{"upper": 0.2, "limit": 0.007, "mode": "abs"},
                       {"upper": inf, "limit": 0.010, "mode": "abs"}]},
    "P,ad": {"bands": [{"upper": 0.2, "limit": 0.007, "mode": "abs"},
                       {"upper": inf, "limit": 0.010, "mode": "abs"}]},
    # Cl: MNS 7057:2024 - 10% (бүх утганд)
    "Cl":   {"single": {"limit": 0.10, "mode": "percent"}},
    "Cl,ad": {"single": {"limit": 0.10, "mode": "percent"}},
    # F: MNS GB/T 4633:2024 - ≤150 ppm бол 15 ppm, >150 ppm бол 10%
    "F":    {"bands": [{"upper": 150.0, "limit": 15.0, "mode": "abs"},
                       {"upper": inf,   "limit": 0.10, "mode": "percent"}]},
    "F,ad": {"bands": [{"upper": 150.0, "limit": 15.0, "mode": "abs"},
                       {"upper": inf,   "limit": 0.10, "mode": "percent"}]},
    "CV":   {"single": {"limit": 120.0, "mode": "abs"}},
    "TRD":  {"single": {"limit": 0.02, "mode": "abs"}},
    "X":    {"bands": [{"upper": 20.0, "limit": 1.0, "mode": "abs"},
                       {"upper": inf,  "limit": 2.0, "mode": "abs"}]},
    "Y":    {"bands": [{"upper": 20.0, "limit": 1.0, "mode": "abs"},
                       {"upper": inf,  "limit": 2.0, "mode": "abs"}]},
}
