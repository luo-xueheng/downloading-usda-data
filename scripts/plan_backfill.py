"""Expand the frozen source scope into a cutoff-bound complete task inventory."""
from pathlib import Path
from datetime import datetime,date,timezone
import calendar,json,shutil
from usda_data.config import DATASETS
from usda_data.sources import wasde,ers_costs_returns,fas_esr,fas_psd,rma_sob,reports
from usda_data.sources.fas_common import client_config,cached_response
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.storage import Store,atomic_write,canonical

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09';STORE=Store(ROOT/'data');cutoff=datetime.now(timezone.utc);today=cutoff.astimezone(__import__('zoneinfo').ZoneInfo('Asia/Shanghai')).date()
tasks=[];expected=[];limitations=[]
def add(id,dataset,options,**meta):
    tasks.append({'task_id':id,'dataset':dataset,'options':options})
    expected.append({'task_id':id,'dataset':dataset,'status':'pending',**meta})
with HTTPClient() as client:
 w=wasde.discover(client,STORE)
 numeric=[r for r in w['links'] if r['format'] in {'csv','zip'}]
 add('wasde-full','wasde',{'start':'2010-01-01','end':today.isoformat()},source_files=len(numeric),estimated_partition_count=200)
 e=ers_costs_returns.discover(client,STORE)
 add('ers-full','costs-returns',{'years':list(range(2010,today.year+6)),'commodities':'all'},source_files=sum(r['selected'] for r in e),note='Source observation years are selected from files; extra upper years only permit already published forecasts, not invented observations.')
with HTTPClient(client_config()) as client:
 d,_=fas_esr.discover(client,STORE,refresh=True)
 latest={str(r['commodityCode']):r['marketYear'] for r in d['datareleasedates']}
 for commodity in d['commodities']:
  code=str(commodity['commodityCode'])
  for year in range(2010,int(latest[code])+1):add(f'esr-{code}-{year}','export-sales',{'commodities':[code],'market_years':[year]},commodity_code=code,market_year=year)
 pdict,_=fas_psd.discover(client,STORE,refresh=True);periods={}
 for code in fas_psd.SCOPE['commodity_union']:
  body,receipt=cached_response(STORE,f'/api/psd/commodity/{code}/dataReleaseDates',client=client,refresh=True)
  rows=fas_psd.release_inventory(body,code);years=sorted({int(r['marketYear']) for r in rows if int(r['marketYear'])>=2010})
  periods[code]={'years':years,'source_artifact_id':receipt['source_artifact_id']}
  print('PSD inventory',code,len(years),flush=True)
 for family in reports.FAMILIES:
  years=sorted({year for c in fas_psd.SCOPE['families'][family]['commodities'] for year in periods[c['commodityCode']]['years']})
  last=calendar.monthrange(today.year,today.month)[1]
  add(f'{family}-full',family,{'market_years':years,'commodities':'all','report_start':'2010-01-01','report_end':today.replace(day=last).isoformat()},source_cutoff_utc=cutoff.isoformat(),report_selection='Only already discovered/downloadable reports at frozen cutoff; end of current month permits month-only publication precision, not future releases',psd_years=years)
 body,receipt=reports.fetch_public(client,STORE,reports.DIRECTORY,'json',refresh=True)
 directory=json.loads(body)
 months={(int(y['CalendarYear']),int(m['Item1'])) for y in directory['CircularSets'] for m in y['Months']}
 for year in range(2010,today.year+1):
  for month in range(1,13):
   if (year,month)>(today.year,today.month):continue
   if (year,month) not in months:limitations.append({'kind':'unlisted_report_month','period':f'{year}-{month:02}','status':'unresolved','reason':'An absent directory entry is not proof of permanent unavailability; independent source evidence required.'})
with HTTPClient(HTTPConfig(trust_environment=False)) as client:
 r=rma_sob.discover(client,STORE,refresh=True)
 for year in sorted(map(int,r['years'])):
  if year>=2010:add(f'rma-{year}','rma-sob',{'commodity_years':[year],'chunk_size':5000},commodity_year=year)
config={'schema_version':1,'description':'Complete frozen seven-dataset backfill from 2010, with exact cutoff and discovered source-year ranges. No development commodity restriction.','scope_mode':'full_frozen_scope','data_dir':'data','output_dir':'data/exports','refresh_policy':'all_configured','memory_budget_mib':1024,'calendar':'config/calendar.json','tasks':tasks}
atomic_write(ROOT/'config/full_backfill.json',canonical(config))
atomic_write(OUT/'expected_tasks.json',canonical(expected));atomic_write(OUT/'psd_period_inventory.json',canonical(periods));atomic_write(OUT/'unresolved_source_gaps.json',canonical(limitations))
estimate={'cutoff_utc':cutoff.isoformat(),'client_cutoff_date':today.isoformat(),'task_count':len(tasks),'esr_partitions':sum(t['dataset']=='export-sales' for t in tasks),'rma_years':sum(t['dataset']=='rma-sob' for t in tasks),'psd_unique_commodity_years':sum(len(p['years']) for p in periods.values()),'report_candidates':sum(y>=2010 and (y,m)<=(today.year,today.month) for y,m in months)*3,'estimated_requests':len(tasks)+2*sum(len(p['years']) for p in periods.values())+3*sum(y>=2010 and (y,m)<=(today.year,today.month) for y,m in months)+200,'estimated_disk_bytes':35_000_000_000,'estimate_method':'Conservative extrapolation of full annual RMA normalized/export sizes, report cells/PDFs, PSD and ESR partitions, with retained versions and temporary outputs. Actual use monitored; stop before exhausting disk.','free_disk_bytes':shutil.disk_usage(ROOT).free,'unresolved_gaps':limitations}
atomic_write(OUT/'resource_estimate.json',canonical(estimate));print(json.dumps(estimate,indent=2))
