"""Manually transcribed and visually verified PDF cells, independent of the parser."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3]
cat=json.loads((ROOT/'tests/fixtures/catalog.json').read_text())['artifacts']
refs=[]
wap={'development':['222.13','220.16','215.12','215.14','3.60','3.83','3.82','3.85','799.02','844.03','822.39','827.51'],'holdout':['222.13','220.16','215.33','215.12','3.60','3.83','3.82','3.82','799.06','844.06','822.43','822.39']}
grain={'development':{'World Total':['790286','791592','799022','844029','822390','827505'],'Australia':['40545','25960','34110','35985','31000','32500']},'holdout':{'World Total':['790286','791593','799059','844057','822432','822390'],'Australia':['40545','25960','34110','35985','31000','31000']}}
oil={'development':{'Production':['378.21','396.54','428.23','429.26','442.70','442.50'],'Ending Stocks':['101.77','115.09','126.01','124.98','124.28','123.50']},'holdout':{'Production':['378.21','396.45','428.11','429.19','442.35','442.70'],'Ending Stocks':['101.84','115.10','125.97','124.93','124.02','124.28']}}
for family in ['world-production','grain-trade','oilseed-trade']:
 for role in ['development','holdout']:
  artifact=next(a for a in cat if a['artifact_id']==f'{family}-{role}')
  previous,current=('Oct','Nov') if role=='development' else ('Sep','Oct')
  entries=[]
  if family=='world-production':
   periods=['2024/25','2025/26','2026/27','2026/27'];months=['not_applicable','not_applicable',previous,current]
   for i,value in enumerate(wap[role]):
    metric=['Area','Yield','Production'][i//4];unit=['Million hectares','Metric tons per hectare','Million metric tons'][i//4]
    entries.append(dict(table_title='Table 02 Wheat Area, Yield, and Production',section_label='not_applicable',row_label='World',indicator=metric,period_label=periods[i%4],comparison_label=months[i%4],unit=unit,value=value,page=20 if role=='development' else 22))
  elif family=='grain-trade':
   periods=['2022/23','2023/24','2024/25','2025/26','2026/27','2026/27'];months=['not_applicable']*4+[previous,current]
   for row,values in grain[role].items():
    for i,value in enumerate(values):entries.append(dict(table_title='World Wheat Production, Consumption, and Stocks',section_label='Production',row_label=row,indicator='Production',period_label=periods[i],comparison_label=months[i],unit='Thousand Metric Tons',value=value,page=18 if role=='development' else 20))
  else:
   periods=['2022/23','2023/24','2024/25','2025/26','2026/27','2026/27'];months=['not_applicable']*4+[previous,current]
   for metric,values in oil[role].items():
    for i,value in enumerate(values):entries.append(dict(table_title='Table 01: Major Oilseeds: World Supply and Distribution (Commodity View)',section_label=metric,row_label='Oilseed, Soybean',indicator=metric,period_label=periods[i],comparison_label=months[i],unit='Million Metric Tons',value=value,page=10))
  for i,entry in enumerate(entries):
   refs.append({'reference_id':f'{family}-{role}-{i+1}','family':family,'role':role,'artifact':artifact['path'],'sha256':artifact['sha256'],'source_url':artifact['url'],'report_period':artifact['vintage'],'method':'Manual transcription from visually reviewed rendered PDF page; values frozen before production report parser implementation','tolerance':'0',**entry})
(ROOT/'tests/fixtures/phase_06/references.json').write_text(json.dumps(refs,indent=2)+'\n')
print('Frozen manual references',len(refs))
