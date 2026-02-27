import pandas as pd, json
path=r"D:\coal_lims_project\SOP\water\LIMS_Water chem lab updated by Otgontsetseg.xlsx"
sheet='Бохир усны шинжилгээний үр дүн'
df=pd.read_excel(path, sheet_name=sheet, header=None)
keywords=['Хлорид','Умбуур','БХХ','БХХ5','Аммоний','Нитрит','Фосфат','Төмөр']
rows=[]
for i,row in df.iterrows():
    line=' '.join(str(x) for x in row.tolist())
    for k in keywords:
        if k in line:
            rows.append((i,k))
            break
print(json.dumps(rows, ensure_ascii=True))
for i,k in rows:
    start=max(0,i-3); end=min(len(df), i+15)
    block=df.iloc[start:end].fillna('')
    out=[]
    for r in range(start,end):
        rowvals=block.loc[r].tolist()[:12]
        out.append([r,rowvals])
    print(json.dumps({'k':k,'row':i,'block':out}, ensure_ascii=True))
