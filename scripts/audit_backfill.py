"""Compare frozen independent numeric references with the active backfill outputs."""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import csv, json
from usda_data.storage import hash_file, canonical, atomic_write
from usda_data.sources.report_tables import parse_report

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    active=json.loads((ROOT/'data/manifests/runs/active.json').read_text())
    state=json.loads((ROOT/'data/manifests/runs'/f'{active["run_id"]}.json').read_text())
    refs=json.loads((ROOT/'tests/fixtures/phase_09/numeric_audit_references.json').read_text())['references']
    refs+=json.loads((ROOT/'tests/fixtures/phase_09/numeric_audit_supplement.json').read_text())['references']
    groups=defaultdict(list);checks=[]
    for ref in refs:
        dataset=ref['dataset']
        task='wasde-full' if dataset=='wasde' else 'ers-full' if dataset=='costs-returns' else f'rma-{ref["commodity_year"]}' if dataset=='rma-sob' else f'esr-{ref["dimensions"]["commodityCode"]}-{ref["market_year"]}'
        groups[task].append(ref)
    for task,items in groups.items():
        entry=state['tasks'][task]
        if entry['status']!='succeeded':raise RuntimeError('Audit partition not yet available: '+task)
        export=entry['export'];path=ROOT/'data/exports'/export['csv_path']
        if hash_file(path)!=export['csv_sha256']:raise RuntimeError('Audit export hash mismatch')
        found=defaultdict(list)
        for row in csv.DictReader(path.open(newline='')):
            for ref in items:
                if row['source_artifact_id']!=ref['source_artifact_id']:continue
                d=ref['dimensions'];dataset=ref['dataset']
                if dataset=='wasde':
                    keys=['WasdeNumber','ReportTitle','Attribute','Commodity','Region','MarketYear','Unit','ReleaseDate','ForecastYear','ForecastMonth']
                    match=all(row[k]==str(d[k]).strip() for k in keys)
                elif dataset=='costs-returns':
                    match=json.loads(row['source_locator']).get('record')==ref['source_locator']['csv_record_including_header']
                elif dataset=='rma-sob':match=int(row['source_line'])==ref['source_locator']['line'] and row['source_member']==ref['source_locator']['member']
                else:match=all(row[k]==(str(v)[:10] if k=='weekEndingDate' else str(v)) for k,v in d.items()) and row['marketYear']==ref['market_year']
                if match:found[ref['id']].append(row)
        for ref in items:
            rows=found[ref['id']];actual=rows[0][ref['field']] if len(rows)==1 else None
            ok=actual is not None and Decimal(actual)==Decimal(ref['expected_value'])
            if ok and ref.get('unit') and ref['dataset']!='rma-sob':ok=rows[0]['Unit' if ref['dataset']=='wasde' else 'unit']==ref['unit']
            checks.append({'reference_id':ref['id'],'dataset':ref['dataset'],'source_artifact_id':ref['source_artifact_id'],'source_locator':json.dumps(ref['source_locator']), 'expected_value':ref['expected_value'],'actual_value':actual,'matches':len(rows),'status':'pass' if ok else 'fail','comparison_target':str(path.relative_to(ROOT))})
        print(task,Counter(c['status'] for c in checks),flush=True)
    report_refs=json.loads((ROOT/'tests/fixtures/phase_09/report_audit_references.json').read_text())
    report_groups=defaultdict(list)
    for ref in report_refs:report_groups[(ref['dataset'],ref['artifact'])].append(ref)
    for (family,artifact),items in report_groups.items():
        source=ROOT/artifact;digest=hash_file(source)
        if any(r['sha256']!=digest for r in items):raise RuntimeError('Frozen reference artifact changed')
        receipt={'source_artifact_id':digest,'retrieved_at_utc':'2026-11-16T00:00:00+00:00'}
        try:frame,_=parse_report(source.read_bytes(),family,receipt,expected_period=items[0]['source_report_period'])
        except Exception as exc:
            for ref in items:checks.append({'reference_id':ref['reference_id'],'dataset':family,'source_artifact_id':digest,'source_locator':f'page {ref["source_page"]}','expected_value':ref['expected_value'],'actual_value':None,'matches':0,'status':'fail','comparison_target':artifact,'error':str(exc)})
            continue
        for ref in items:
            selected=frame
            for key in ['table_title','row_label','indicator','comparison_label','section_label','period_label','column_commodity']:
                if key in ref:selected=selected[selected[key]==ref[key]]
            selected=selected[selected.source_page==ref['source_page']]
            actual=str(selected.iloc[0]['value']) if len(selected)==1 else None
            ok=actual is not None and Decimal(actual)==Decimal(ref['expected_value']) and selected.iloc[0]['unit']==ref['expected_unit']
            checks.append({'reference_id':ref['reference_id'],'dataset':family,'source_artifact_id':digest,'source_locator':f'page {ref["source_page"]}','expected_value':ref['expected_value'],'actual_value':actual,'matches':len(selected),'status':'pass' if ok else 'fail','comparison_target':'Parser replay of frozen source; full export linkage remains separately gated'})
        print(family,artifact,flush=True)
    fields=['reference_id','dataset','source_artifact_id','source_locator','expected_value','actual_value','matches','status','comparison_target','error']
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(checks)
    result={'checks':len(checks),'counts':dict(Counter(c['status'] for c in checks)),'per_dataset':{d:dict(Counter(c['status'] for c in checks if c['dataset']==d)) for d in sorted({c['dataset'] for c in checks})},'report_export_linkage':'pending complete report backfill'}
    atomic_write(OUT/'independent_audit.json',canonical(result));print(result)
    return int(any(c['status']!='pass' for c in checks))

if __name__=='__main__':raise SystemExit(main())
