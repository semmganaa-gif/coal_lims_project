# app/constants/nomenclature.py
"""Нүүрсний шинжилгээний нэршил — subscript mapping."""

# fmt_code filter-д ашиглах subscript mapping
# key: normalized code (lowercase), value: (prefix, subscript)
# HTML output: prefix + <sub>subscript</sub>
ANALYSIS_CODE_SUBSCRIPTS = {
    # --- Чийг (Moisture) ---
    'mt':       ('M', 'T,ar'),
    'mt,ar':    ('M', 'T,ar'),
    'mad':      ('M', 'ad'),
    'm,ad':     ('M', 'ad'),
    'fm':       ('FM', ''),

    # --- Үнслэг (Ash) ---
    'aad':      ('A', 'ad'),
    'a,ad':     ('A', 'ad'),
    'a,ar':     ('A', 'ar'),
    'a,d':      ('A', 'd'),
    'ad':       ('A', 'd'),

    # --- Дэгдэмхий бодис (Volatile Matter) ---
    'vad':      ('V', 'ad'),
    'v,ad':     ('V', 'ad'),
    'v,ar':     ('V', 'ar'),
    'v,d':      ('V', 'd'),
    'vdaf':     ('V', 'daf'),
    'v,daf':    ('V', 'daf'),

    # --- Холбоот нүүрстөрөгч (Fixed Carbon) ---
    'fcd':      ('FC', 'd'),
    'fc,d':     ('FC', 'd'),
    'fcad':     ('FC', 'ad'),
    'fc,ad':    ('FC', 'ad'),

    # --- Хүхэр (Sulfur) ---
    'ts':       ('S', 't'),
    'st,ad':    ('S', 't,ad'),
    'st,d':     ('S', 't,d'),
    's,t,ad':   ('S', 't,ad'),
    's,t,d':    ('S', 't,d'),

    # --- Илчлэг (Calorific Value) ---
    'cv':       ('Q', 'gr,ad'),
    'qgr,ad':   ('Q', 'gr,ad'),
    'qgr,ar':   ('Q', 'gr,ar'),
    'qgr,d':    ('Q', 'gr,d'),
    'qnet,ar':  ('Q', 'net,ar'),

    # --- Коксжих чанар (Coking Properties) ---
    'csn':      ('CSN', ''),
    'gi':       ('G', 'i'),
    'x':        ('X', ''),
    'y':        ('Y', ''),

    # --- Харьцангуй нягт (Relative Density) ---
    'trd':      ('TRD', 'ad'),
    'trd,ad':   ('TRD', 'ad'),
    'trd,d':    ('TRD', 'd'),

    # --- Бичил элементүүд (Trace Elements) ---
    'p':        ('P', 'ad'),
    'p,ad':     ('P', 'ad'),
    'p,d':      ('P', 'd'),
    'f':        ('F', 'ad'),
    'f,ad':     ('F', 'ad'),
    'f,d':      ('F', 'd'),
    'cl':       ('Cl', 'ad'),
    'cl,ad':    ('Cl', 'ad'),
    'cl,d':     ('Cl', 'd'),

    # --- CRI/CSR ---
    'cri':      ('CRI', ''),
    'csr':      ('CSR', ''),
    'cricsr':   ('CRI/CSR', ''),

    # --- WTL MG ---
    'mg':       ('MG', ''),
    'mg_size':  ('MG', 'Size'),
}
