"""
Process BMUFuelType.xlsx → bmu_fuel_types.json
Run from the ispstack-viewer directory: python3 process_bmu.py
"""
import pandas as pd
import json
import re

FUEL_COLOURS = {
    'BATTERY':       '#FFAAAA',
    'CCGT':          '#C4AAEE',
    'BIOMASS':       '#B07070',
    'WIND':          '#AADDAA',
    'PS':            '#AABBEE',
    'NPSHYD':        '#AADDEE',
    'OCGT':          '#EEEEAA',
    'SOLAR':         '#FFCCAA',
    'LOAD RESPONSE': '#FFBBDD',
    'GAS':           '#CCAA88',
    'DIESEL':        '#CCAA88',
    'NUCLEAR':       '#BBBBBB',
}
DEFAULT_COLOUR = '#BBBBBB'  # Other / unknown

DISPLAY_LABELS = {
    'BATTERY':       'Battery',
    'CCGT':          'CCGT',
    'BIOMASS':       'Biomass',
    'WIND':          'Wind',
    'PS':            'Pumped Storage',
    'NPSHYD':        'NPSHYD',
    'OCGT':          'OCGT',
    'SOLAR':         'Solar',
    'LOAD RESPONSE': 'Load Response',
    'GAS':           'Gas / Diesel',
    'DIESEL':        'Gas / Diesel',
    'NUCLEAR':       'Nuclear',
    'OTHER':         'Other',
}

df = pd.read_excel('BMUFuelType.xlsx')

# Extract last updated date from column headers (stored as "Updated: DD/MM/YYYY")
updated_date = None
for col in df.columns:
    m = re.search(r'Updated:\s*(\d{2}/\d{2}/\d{4})', str(col))
    if m:
        updated_date = m.group(1)
        break

print(f"Source last updated: {updated_date or 'unknown'}")

records = {}
for _, row in df.iterrows():
    reg  = str(row.get('REG FUEL TYPE',  '')).strip().upper() if pd.notna(row.get('REG FUEL TYPE'))  else ''
    bmrs = str(row.get('BMRS FUEL TYPE', '')).strip().upper() if pd.notna(row.get('BMRS FUEL TYPE')) else ''

    key    = reg if reg in FUEL_COLOURS else (bmrs if bmrs in FUEL_COLOURS else (reg or bmrs or 'OTHER'))
    colour = FUEL_COLOURS.get(key, DEFAULT_COLOUR)
    label  = DISPLAY_LABELS.get(key, key.title() if key else 'Other')

    entry = {
        'label':        label,
        'regFuelType':  reg,
        'bmrsFuelType': bmrs,
        'colour':       colour,
        'gcOc2':        str(row.get('GC OC2', '')).strip().upper() == 'YES',
    }

    # Primary key: SETT UNIT ID (matches the ID used in the BMRS API)
    sett_id = row.get('SETT UNIT ID')
    if pd.notna(sett_id) and str(sett_id).strip():
        records[str(sett_id).strip()] = entry

    # Secondary key: NESO BMU ID (fallback for units without a settlement ID)
    neso_id = str(row.get('NESO BMU ID', '')).strip()
    if neso_id and neso_id not in records:
        records[neso_id] = entry

output = {
    '_meta': {
        'sourceUpdated': updated_date,
        'recordCount':   len(records),
    },
    'bmu': records,
}

with open('bmu_fuel_types.js', 'w') as f:
    f.write('window.BMU_FUEL_DATA=')
    json.dump(output, f, separators=(',', ':'))
    f.write(';')

print(f"Exported {len(records)} records (SETT UNIT ID + NESO BMU ID) to bmu_fuel_types.js")

from collections import Counter
counts = Counter(v['label'] for v in records.values())
for label, count in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {label:20s}  {count:4d}")
