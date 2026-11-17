"""Freeze direct official JSON field observations before the PSD parser exists."""
from pathlib import Path
import json,hashlib
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[3];FIX=ROOT/'tests/fixtures/phase_05'
units={str(r['unitId']):r['unitDescription'].strip() for r in json.loads((FIX/'unitsOfMeasure.json').read_text())}
refs=[];catalog=[]
for job in json.loads((ROOT/'artifacts/acceptance/phase-05/numeric_jobs.json').read_text()):
 if not job['id'].startswith(('psd-','world-')):continue
 p=FIX/(job['id']+'.json');body=p.read_bytes();rows=json.loads(body,parse_float=Decimal);sha=hashlib.sha256(body).hexdigest()
 countries=['00'] if job['id'].startswith('world-') else ['US','BR']
 attrs=[4,28,184] if job['role']=='holdout' else [20,28,57,88,176]
 for country in countries:
  for attr in attrs:
   i,row=next((i,r) for i,r in enumerate(rows) if r['countryCode']==country and r['attributeId']==attr)
   refs.append({'id':f'{job["id"]}:{country}:{attr}','role':job['role'],'artifact':str(p.relative_to(ROOT)),'sha256':sha,'source_url':'https://api.fas.usda.gov'+job['path'],'locator':{'array_index':i,'field':'value'},'dimensions':{k:v for k,v in row.items() if k!='value'},'expected_value':str(row['value']),'expected_unit':units[str(row['unitId'])],'method':'Independent standard-library JSON decoding with Decimal, fixed geography/attribute selection before adapter implementation','tolerance':'0'})
 catalog.append({'id':job['id'],'role':job['role'],'artifact':str(p.relative_to(ROOT)),'sha256':sha,'expected_records':len(rows),'selected_before_adapter':True,'first_adapter_run':'not_run'})
(FIX/'references.json').write_text(json.dumps(refs,indent=2)+'\n');(FIX/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
(FIX/'balance_rules.json').write_text(json.dumps({'selected_before_tests':True,'commodity':'0440000','country':'US','years':[2024,2025],'formulas':[{'left':[20,28,57],'right':[86]},{'left':[88,125,176],'right':[178]},{'left':[86],'right':[178]}],'unitId':'8','tolerance':'0','reason':'Source local marketing-year supply and distribution identity for US corn; TY imports/exports are intentionally not mixed with MY measures.'},indent=2)+'\n')
print('Frozen PSD references:',len(refs))
