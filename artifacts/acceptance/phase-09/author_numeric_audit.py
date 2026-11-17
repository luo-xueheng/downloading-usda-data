"""Freeze stratified extra numeric references directly from full-run raw sources.

Never read normalized output or call a production parser when creating expectations.
"""
from pathlib import Path
from decimal import Decimal
import json,csv,io,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'data';refs=[]
def raw(id):
 p=DATA/'raw'/id[:2]/id
 assert hashlib.sha256(p.read_bytes()).hexdigest()==id
 return p
# ESR: early/middle/recent years plus a non-default commodity, all raw responses already acquired.
for code,year in [('107',2010),('401',2018),('801',2026),('701',2026)]:
 manifest=json.loads((DATA/f'manifests/export-sales/{code}-{year}.latest.json').read_text())
 candidates=[]
 for id in manifest['source_artifact_ids']:
  obj=json.loads(raw(id).read_bytes())
  if isinstance(obj,list) and obj and 'weeklyExports' in obj[0]:candidates.append((id,obj))
 assert len(candidates)==1;id,rows=candidates[0]
 for index in [len(rows)//5,2*len(rows)//5,3*len(rows)//5,4*len(rows)//5,len(rows)-1]:
  r=rows[index];refs.append({'id':f'esr-{code}-{year}-{index}','dataset':'export-sales','source_artifact_id':id,'raw_path':str(raw(id).relative_to(ROOT)),'source_locator':{'array_index':index,'field':'outstandingSales'},'dimensions':{k:r[k] for k in ['commodityCode','countryCode','unitId','weekEndingDate']},'market_year':str(year),'field':'outstandingSales','expected_value':str(r['outstandingSales']),'method':'Independent standard-library JSON read; fixed stratified positions before output comparison'})
# ERS: multiple commodities and observation-year strata, exact long CSV source dimensions.
for id,year in [('4962',2010),('4962',2018),('4964',2025),('4980',2025)]:
 p=next((ROOT/'tests/fixtures/phase_03').glob(id+'-*.csv'));a=json.loads(Path(str(p)+'.acquisition.json').read_text());rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
 found=[(i,r) for i,r in enumerate(rows,2) if r['Year']==str(year)]
 for index in [len(found)//6,2*len(found)//6,3*len(found)//6,4*len(found)//6,5*len(found)//6]:
  line,r=found[index];refs.append({'id':f'ers-{id}-{year}-{line}','dataset':'costs-returns','source_artifact_id':a['sha256'],'raw_path':str(p.relative_to(ROOT)),'source_locator':{'csv_record_including_header':line},'dimensions':{k:v for k,v in r.items() if k!='Value'},'field':'value','expected_value':r['Value'],'unit':r['Units'],'method':'Independent CSV read; two time strata and nondevelopment cotton/milk before output comparison'})
# WASDE: frozen early/middle/recent file sources; select multiple tables including non-crop.
for year,month in [(2010,4),(2018,6),(2026,11)]:
 manifest=json.loads((DATA/f'manifests/wasde/{year}-{month:02}-'+('09' if year==2010 else '12' if year==2018 else '10')+'.latest.json').read_text()) if False else None
 # Select artifacts from verified URL receipts, not normalized values.
 receipts=[json.loads(p.read_text()) for p in (DATA/'manifests/wasde/urls').glob('*.json')]
 key='2010-04-to-2015-12' if year==2010 else '2016-01-to-2020-12' if year==2018 else '2026-11.csv'
 a=next(r for r in receipts if key in r['url']);p=raw(a['source_artifact_id'])
 if p.read_bytes()[:2]==b'PK':
  with zipfile.ZipFile(p) as z:member=z.namelist()[0];rows=list(csv.DictReader(io.TextIOWrapper(z.open(member),encoding='utf-8-sig')))
 else:member='';rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
 for fragment in ['World Corn Supply','U.S. Milk','U.S. Sugar','U.S. Wheat']:
  matches=[(i,r) for i,r in enumerate(rows,2) if r['ForecastYear']==str(year) and int(r['ForecastMonth'])==month and fragment in r['ReportTitle']]
  for offset in [len(matches)//3,2*len(matches)//3]:
   line,r=matches[offset];refs.append({'id':f'wasde-{year}-{month}-{line}','dataset':'wasde','source_artifact_id':a['source_artifact_id'],'raw_path':str(p.relative_to(ROOT)),'source_locator':{'member':member,'csv_record_including_header':line},'dimensions':{k:v for k,v in r.items() if k!='Value'},'field':'Value','expected_value':r['Value'],'unit':r['Unit'],'method':'Independent CSV read; fixed early/middle/recent report months and four table families before output comparison'})
# RMA: two complete source years plus mid-year when available; do not rely on normalized values.
for year,path in [(2010,ROOT/'tests/fixtures/raw/rma-holdout.zip'),(2025,ROOT/'tests/fixtures/raw/rma-development.zip')]:
 a=json.loads(Path(str(path)+'.acquisition.json').read_text())
 with zipfile.ZipFile(path) as z:
  member=z.namelist()[0];rows=list(csv.reader(io.TextIOWrapper(z.open(member),encoding='utf-8-sig'),delimiter='|'))
 for j in range(10):
  index=(j+1)*len(rows)//11;r=rows[index];refs.append({'id':f'rma-{year}-{index+1}','dataset':'rma-sob','source_artifact_id':a['sha256'],'raw_path':str(path.relative_to(ROOT)),'source_locator':{'member':member,'line':index+1,'field_1_based':27},'dimensions':[v.strip() for v in r[:12]+[r[17]]],'commodity_year':str(year),'field':'indemnity_amount','expected_value':r[26].strip(),'unit':'USD','method':'Independent integer pipe field read; fixed rows across geographic/source categories before output comparison'})
result={'frozen_before_output_comparison':True,'reference_count':len(refs),'references':refs}
(ROOT/'tests/fixtures/phase_09/numeric_audit_references.json').write_text(json.dumps(result,indent=2)+'\n')
print('Frozen numerical audit',len(refs))
