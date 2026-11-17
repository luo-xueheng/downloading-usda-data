"""Reconcile saved full-run parser accounting with the frozen source inventory."""
from pathlib import Path
from collections import Counter
import csv,json
from usda_data.storage import Store,sha256,canonical,atomic_write
from usda_data.sources import wasde
from datetime import date,datetime

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    store=Store(ROOT/'data');checks=[]
    config=json.loads((ROOT/'config/full_backfill.json').read_text());tasks={r['task_id']:r for r in config['tasks']}
    active=json.loads((store.root/'manifests/runs/active.json').read_text());state=json.loads((store.root/'manifests/runs'/f'{active["run_id"]}.json').read_text())
    inventory=json.loads((store.root/'manifests/wasde/discovery.json').read_text());start=tasks['wasde-full']['options']['start'];end=tasks['wasde-full']['options']['end'];total=0;dates=set()
    for link in inventory['links']:
        if link['format'] not in {'csv','zip'} or not wasde.relevant(link,date.fromisoformat(start),date.fromisoformat(end)):continue
        receipt=json.loads((store.root/'manifests/wasde/urls'/f'{sha256(link["url"].encode())}.json').read_text());artifact=receipt['source_artifact_id']
        accounting=json.loads((store.root/'manifests/wasde/accounting'/f'{artifact}-{start}-{end}.json').read_text())
        assert accounting['quarantined_rows']==0 and accounting['input_rows']==accounting['mapped_rows']+accounting['excluded_outside_bounds']
        independent_count=0
        with wasde.source_members(store.artifact(artifact)) as members:
            for _,stream in members:
                for row in csv.DictReader(stream):
                    release=row['ReleaseDate'].split('T')[0].split(' ')[0]
                    if '/' in release:release=datetime.strptime(release,'%m/%d/%Y').date().isoformat()
                    if start<=release<=end:dates.add(release);independent_count+=1
        assert independent_count==accounting['mapped_rows']
        total+=independent_count;checks.append({'dataset':'wasde','source_artifact_id':artifact,'input_rows':accounting['input_rows'],'mapped_rows':independent_count,'excluded':accounting['excluded_outside_bounds'],'status':'pass'})
    assert total==state['tasks']['wasde-full']['export']['rows']
    selected_dates={p.name.removesuffix('.latest.json') for p in (store.root/'manifests/wasde').glob('*.latest.json') if start<=p.name.removesuffix('.latest.json')<=end}
    assert dates==selected_dates
    ers=json.loads((store.root/'manifests/costs-returns/discovery.json').read_text());ers_rows=0;ers_years=set();ers_files=0
    for item in ers:
        if not item['selected']:continue
        receipt=json.loads((store.root/'manifests/costs-returns/urls'/f'{sha256(item["url"].encode())}.json').read_text());artifact=receipt['source_artifact_id'];store.artifact(artifact)
        accounting=json.loads((store.root/'manifests/costs-returns/accounting'/f'{artifact}.json').read_text())
        assert accounting['quarantined_rows']==0 and accounting['input_data_cells']==accounting['mapped_rows']
        snapshot=store.latest('costs-returns',item['partition']);assert snapshot['source_artifact_ids']==[artifact] and snapshot['rows']==accounting['mapped_rows']
        selected=0
        with (store.root/snapshot['csv_path']).open(newline='') as stream:
            for row in csv.DictReader(stream):
                year=int(row['year'])
                if year in tasks['ers-full']['options']['years']:selected+=1;ers_years.add(year)
        ers_rows+=selected;ers_files+=1
        checks.append({'dataset':'costs-returns','partition':item['partition'],'source_artifact_id':artifact,'input_rows':accounting['input_data_cells'],'mapped_rows':accounting['mapped_rows'],'selected_rows':selected,'status':'pass'})
    assert ers_rows==state['tasks']['ers-full']['export']['rows']
    rma_inventory=json.loads((store.root/'manifests/rma-sob/discovery.json').read_text());expected_years={int(y) for y in rma_inventory['years'] if int(y)>=2010};actual_years=set()
    for key,task in tasks.items():
        if task['dataset']!='rma-sob':continue
        year=task['options']['commodity_years'][0];snapshot=store.latest('rma-sob',str(year));actual_years.add(year)
        receipt=json.loads((store.root/'manifests/rma-sob/urls'/f'{sha256(rma_inventory["years"][str(year)].encode())}.json').read_text());artifact=receipt['source_artifact_id'];store.artifact(artifact)
        accounting=json.loads((store.root/'manifests/rma-sob/accounting'/f'{year}-{artifact}.json').read_text())
        assert accounting['input_rows']==accounting['mapped_rows']==snapshot['rows']==state['tasks'][key]['export']['rows'] and accounting['quarantined_rows']==0
        checks.append({'dataset':'rma-sob','partition':str(year),'source_artifact_id':artifact,'input_rows':accounting['input_rows'],'mapped_rows':accounting['mapped_rows'],'status':'pass'})
    assert expected_years==actual_years
    psd=json.loads((OUT/'psd_period_inventory.json').read_text());psd_count=0
    for code,entry in psd.items():
        store.artifact(entry['source_artifact_id'])
        for year in entry['years']:
            snapshot=store.latest('psd',f'{code}-{year}');assert snapshot is not None
            accounting=json.loads((store.root/'manifests/psd/accounting'/f'{code}-{year}-{snapshot["snapshot_id"]}.json').read_text())
            count=0;excluded=0;inputs=0
            for geo in ['all','world']:
                a=accounting[geo];ex=sum(a['excluded_attributes'].values());assert a['input_records']==a['mapped_records']+ex
                count+=a['mapped_records'];excluded+=ex;inputs+=a['input_records']
            assert count==snapshot['rows'];psd_count+=1
            checks.append({'dataset':'psd','partition':f'{code}-{year}','source_artifact_ids':snapshot['source_artifact_ids'],'input_rows':inputs,'mapped_rows':count,'excluded_attributes':excluded,'status':'pass'})
    boundaries={'wasde':{'earliest':min(dates),'latest':max(dates),'partitions':len(dates),'unsupported_earlier':'2010-01 through 2010-03: official structured archive begins in 2010-04; original earlier layouts remain outside implemented structured history','source_inventory':'data/manifests/wasde/discovery.json'},'costs-returns':{'earliest':min(ers_years),'latest':max(ers_years),'selected_files':ers_files,'all_main_page_links':len(ers),'source_inventory':'data/manifests/costs-returns/discovery.json'},'rma-sob':{'earliest':min(actual_years),'latest':max(actual_years),'partitions':len(actual_years),'source_inventory':'data/manifests/rma-sob/discovery.json'},'psd':{'expected_commodity_year_partitions':sum(len(r['years']) for r in psd.values()),'verified_partitions':psd_count,'commodities':len(psd),'source_inventory':'artifacts/acceptance/phase-09/psd_period_inventory.json'}}
    atomic_write(OUT/'source_accounting.json',canonical({'status':'pass','checked_partitions':len(checks),'boundaries':boundaries,'checks':checks,'scope':'All frozen WASDE numeric sources, selected ERS files, discovered RMA years, and PSD commodity-year inventories; ESR exact source row counts are in empty_source_evidence/coverage reconciliation and all 782 tasks.'}))
    print(boundaries)

if __name__=='__main__':main()
