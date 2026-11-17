"""Independently freeze exact JSON metric values before implementing the ESR parser."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];FIX=ROOT/'tests/fixtures/phase_04'
refs=[];catalog=[]
units={r['unitId']:r['unitNames'] for r in json.loads((FIX/'unitsOfMeasure.json').read_text())}
metrics=['weeklyExports','accumulatedExports','outstandingSales','currentMYNetSales','nextMYNetSales']
for job in json.loads((ROOT/'artifacts/acceptance/phase-04/numeric_jobs.json').read_text()):
 p=FIX/(job['id']+'.json');raw=p.read_bytes();rows=json.loads(raw);a=json.loads(Path(str(p)+'.acquisition.json').read_text());year=int(job['id'].split('-')[-1]);destinations=sorted({r['countryCode'] for r in rows})[:2]
 chosen=[next((i,r) for i,r in enumerate(rows) if r['countryCode']==country) for country in destinations]
 for i,row in chosen:
  for metric in metrics:
   refs.append({'reference_id':f'{job["id"]}:{i}:{metric}','role':job['role'],'artifact':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'source_url':job['path'],'locator':{'array_index':i,'field':metric},'dimensions':{k:row[k] for k in ['commodityCode','countryCode','unitId','weekEndingDate']},'market_year':str(year),'unit':units[row['unitId']],'expected_value':str(row[metric]),'method':'Independent standard-library JSON decoding and direct source field selection before production parser; exact equality'})
 negative=next(((i,r) for i,r in enumerate(rows) if r['currentMYNetSales']<0),None)
 if negative:
  i,row=negative;refs.append({'reference_id':f'{job["id"]}:negative','role':job['role'],'artifact':str(p.relative_to(ROOT)),'sha256':a['sha256'],'source_url':job['path'],'locator':{'array_index':i,'field':'currentMYNetSales'},'dimensions':{k:row[k] for k in ['commodityCode','countryCode','unitId','weekEndingDate']},'market_year':str(year),'unit':units[row['unitId']],'expected_value':str(row['currentMYNetSales']),'method':'Independent first real cancellation/negative net-sales record; no parser import'})
 catalog.append({'id':job['id'],'role':job['role'],'artifact':str(p.relative_to(ROOT)),'sha256':a['sha256'],'expected_records':len(rows),'selected_before_adapter':True,'first_adapter_run':'not_run'})
(FIX/'references.json').write_text(json.dumps(refs,indent=2)+'\n');(FIX/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
print('Frozen references',len(refs))
