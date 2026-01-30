# -*- coding: utf-8 -*-
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = r'D:\icpms\#25_45_PR12_B23_ST129_4A.xlsx'

print('=== FLOAT SINK SHEET ===')
df = pd.read_excel(file_path, sheet_name='Float sink', header=None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 100)
print(df.to_string())
print()
print(f'Shape: {df.shape}')
print()

print('=== PRETREATMENT SHEET ===')
df2 = pd.read_excel(file_path, sheet_name='Pretreatment', header=None)
print(df2.to_string())
print()
print(f'Shape: {df2.shape}')
