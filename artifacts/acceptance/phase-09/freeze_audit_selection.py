"""Freeze additional independent audit locators before examining backfill output."""
from pathlib import Path
import json,hashlib,csv,io,zipfile
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'tests/fixtures/phase_09';out.mkdir(parents=True,exist_ok=True)
# Source selection uses only input cells and excludes every development-reference locator.
selections=[]
for dataset,phase in [('export-sales','04'),('world-production','06'),('grain-trade','06'),('oilseed-trade','06')]:
 if phase=='04':
  existing=json.loads((ROOT/'tests/fixtures/phase_04/references.json').read_text());used={(r['artifact'],r['locator']['array_index'],r['locator']['field']) for r in existing}
  for code,year in [(107,2025),(401,2026),(801,2025),(701,2026)]:
   name=f'tests/fixtures/phase_04/esr-{code}-{year}.json';rows=json.loads((ROOT/name).read_text());sha=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
   for i in [len(rows)//4,len(rows)//2,3*len(rows)//4,len(rows)-1,len(rows)-2]:
    metric='outstandingSales';assert (name,i,metric) not in used
    selections.append({'dataset':dataset,'artifact':name,'sha256':sha,'locator':{'array_index':i,'field':metric},'expected_value':str(rows[i][metric]),'dimensions':{k:rows[i][k] for k in ['commodityCode','countryCode','unitId','weekEndingDate']},'source_marketing_year':str(year),'method':'Independent source JSON cell selection; frozen before full-output inspection; not parser-generated'})
 else:
  # New table/page/geography/indicator selections, deliberately distinct from the
  # 72 earlier World Wheat/Oilseed Soybean reference cells.
  for role in ['development','holdout']:
   name=f'tests/fixtures/raw/{dataset}-{role}.pdf';sha=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
   for i in range(10):
    selections.append({'dataset':dataset,'artifact':name,'sha256':sha,'locator':{'table':'Table 04 Corn Area, Yield, and Production' if dataset=='world-production' else 'World Corn Production, Consumption, and Stocks' if dataset=='grain-trade' else 'Table 11: Palm Oil: World Supply and Distribution','row_selection':i,'column':'current production'},'expected_value_status':'requires independent visual transcription before comparison','method':'Stratified report-table selection fixed before full-output inspection; numeric expectations not yet authored'})
# Remaining datasets: raw cell/record positions excluded from earlier reference sets.
for dataset,name in [('wasde','tests/fixtures/phase_02/early-cdn.zip'),('costs-returns','tests/fixtures/phase_03/4962-corn.csv'),('rma-sob','tests/fixtures/raw/rma-development.zip')]:
 body=(ROOT/name).read_bytes();sha=hashlib.sha256(body).hexdigest()
 if dataset=='wasde':
  with zipfile.ZipFile(io.BytesIO(body)) as z:
   member=z.namelist()[0];rows=list(csv.DictReader(io.TextIOWrapper(z.open(member),encoding='utf-8-sig')))
  for i in [200+15000*j for j in range(20)]:
   r=rows[i];selections.append({'dataset':dataset,'artifact':name,'sha256':sha,'locator':{'member':member,'csv_record_including_header':i+2,'field':'Value'},'expected_value':r['Value'],'dimensions':{k:v for k,v in r.items() if k!='Value'},'method':'Independent raw CSV reading, 20 positions spanning early/middle archive; not production parser'})
 elif dataset=='costs-returns':
  rows=list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
  for i in [100+250*j for j in range(20)]:
   r=rows[i];selections.append({'dataset':dataset,'artifact':name,'sha256':sha,'locator':{'csv_record_including_header':i+2,'field':'Value'},'expected_value':r['Value'],'dimensions':{k:v for k,v in r.items() if k!='Value'},'method':'Independent raw CSV reading; positions frozen before full-output inspection'})
 else:
  with zipfile.ZipFile(io.BytesIO(body)) as z:
   member=z.namelist()[0];rows=list(csv.reader(io.TextIOWrapper(z.open(member),encoding='utf-8-sig'),delimiter='|'))
  for i in [10000+6000*j for j in range(20)]:
   r=rows[i];selections.append({'dataset':dataset,'artifact':name,'sha256':sha,'locator':{'member':member,'line':i+1,'field_1_based':27},'expected_value':r[26].strip(),'dimensions':r[:12]+[r[17]],'method':'Independent raw pipe-field reading, distinct from development references'})
(out/'audit_selection.json').write_text(json.dumps({'frozen_before_backfill_output':True,'minimum_per_dataset':20,'status':'selection frozen; some report expectations and additional early/mid/recent geography strata still required before acceptance','selections':selections},indent=2)+'\n')
print('Frozen candidate audit cells',len(selections))
