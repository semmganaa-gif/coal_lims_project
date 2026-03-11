# app/constants/qc_specs.py
"""Name/Class QC Master Specs, Spec Bands, Summary View Columns."""

NAME_CLASS_MASTER_SPECS = {
    "UHG MV_HCC": {
        "Mad": 0.80, "Aad": 10.70, "Vdaf": 27.00,
        "Qnet,ar": None, "CSN": None, "Gi": 80.0,
    },
    "UHG HV_HCC": {
        "Mad": 1.00, "Aad": 11.00, "Vdaf": 30.00,
        "Qnet,ar": None, "CSN": None, "Gi": 87.0,
    },
    "UHG MASHCC": {
        "Mad": 0.50, "Aad": 25.00, "Vdaf": 15.00,
        "Qnet,ar": None, "CSN": None, "Gi": 22.0,
    },
    "BN HV HCC": {
        "Mad": 1.20, "Aad": 12.00, "Vdaf": 32.00,
        "Qnet,ar": None, "CSN": None, "Gi": 90.0,
    },
    "BN SSCC": {
        "Mad": 1.50, "Aad": 9.00, "Vdaf": 27.00,
        "Qnet,ar": None, "CSN": None, "Gi": 88.0,
    },
    "UHG MASHCC_2": {
        "Mad": 0.60, "Aad": 25.00, "Vdaf": 35.00,
        "Qnet,ar": None, "CSN": None, "Gi": 18.0,
    },
    "UHG Midd": {
        "Mad": 0.50, "Aad": 30.00, "Vdaf": 22.00,
        "Qnet,ar": None, "CSN": None, "Gi": 10.0,
    },
    "BN MASHCC_2": {
        "Mad": 0.70, "Aad": 25.00, "Vdaf": 30.00,
        "Qnet,ar": None, "CSN": None, "Gi": 25.0,
    },
    "BN Midd": {
        "Mad": 0.50, "Aad": 30.00, "Vdaf": 22.00,
        "Qnet,ar": None, "CSN": None, "Gi": 10.0,
    },
}

NAME_CLASS_SPEC_BANDS = {
    "Mad": 0.2,
    "Aad": 2.0,
    "Vdaf": 3.0,
    "Qnet,ar": 200.0,
    "CSN": 1.0,
    "Gi": 5.0,
}

SUMMARY_VIEW_COLUMNS = [
    {"code": "MT", "canonical_base": "total_moisture"},
    {"code": "Mad", "canonical_base": "inherent_moisture"},
    {"code": "Aad", "canonical_base": "ash"},
    {"code": "Ad", "canonical_base": "ash"},
    {"code": "Vad", "canonical_base": "volatile_matter"},
    {"code": "Vdaf", "canonical_base": "volatile_matter"},
    {"code": "FC,ad", "canonical_base": "fixed_carbon_ad"},
    {"code": "St,ad", "canonical_base": "total_sulfur"},
    {"code": "St,d", "canonical_base": "total_sulfur"},
    {"code": "Qgr,ad", "canonical_base": "calorific_value"},
    {"code": "Qgr,ar", "canonical_base": "calorific_value"},
    {"code": "Qnet,ar", "canonical_base": "calorific_value"},
    {"code": "CSN", "canonical_base": "free_swelling_index"},
    {"code": "Gi", "canonical_base": "caking_power"},
    {"code": "TRD,ad", "canonical_base": "relative_density"},
    {"code": "TRD,d", "canonical_base": "relative_density"},
    {"code": "P,ad", "canonical_base": "phosphorus"},
    {"code": "P,d", "canonical_base": "phosphorus"},
    {"code": "Solid", "canonical_base": "solid"},
    {"code": "FM", "canonical_base": "free_moisture"},
    {"code": "F,ad", "canonical_base": "total_fluorine"},
    {"code": "F,d", "canonical_base": "total_fluorine"},
    {"code": "Cl,ad", "canonical_base": "total_chlorine"},
    {"code": "Cl,d", "canonical_base": "total_chlorine"},
    {"code": "X", "canonical_base": "plastometer_x"},
    {"code": "Y", "canonical_base": "plastometer_y"},
    {"code": "CRI", "canonical_base": "coke_reactivity_index"},
    {"code": "CSR", "canonical_base": "coke_strength_after_reaction"},
    {"code": "m", "canonical_base": "mass"},
    {"code": "MG", "canonical_base": "mg_magnetic"},
]
