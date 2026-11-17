"""Reconcile the frozen inventory without hiding empty responses or stale report checks."""
from collections import Counter,defaultdict
from pathlib import Path
import csv,json
from usda_data.storage import canonical,atomic_write,sha256,hash_file,Store
from usda_data.sources.fas_esr import path_for
from usda_data.sources.fas_common import BASE

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    store=Store(ROOT/'data');active=json.loads((store.root/'manifests/runs/active.json').read_text())
    state=json.loads((store.root/'manifests/runs'/f'{active["run_id"]}.json').read_text())
    expected=json.loads((OUT/'expected_tasks.json').read_text())
    if {r['task_id'] for r in expected}!=set(state['tasks']):raise ValueError('Run task inventory differs from frozen expectations')
    rows=[];empty=[];bounds=defaultdict(list)
    for item in expected:
        task=state['tasks'][item['task_id']];status=task['status'];reason=task.get('controlled_error','');source='';count=task.get('export',{}).get('rows')
        if status=='succeeded' and item['dataset']=='export-sales':
            options=task['definition']['options'];code=options['commodities'][0];year=options['market_years'][0]
            url=BASE+path_for(code,year);receipt=json.loads((store.root/'manifests/fas/urls'/f'{sha256(url.encode())}.json').read_text());source=receipt['source_artifact_id']
            raw=json.loads(store.artifact(source).read_text())
            if len(raw)!=count:raise ValueError('ESR complete all-country response/export row mismatch')
            if count==0:
                empty.append({'task_id':item['task_id'],'commodity_code':code,'market_year':year,'url':url,'source_artifact_id':source,'response':[],'status':'source_available_empty_at_cutoff','meaning':'A valid archived API response contains zero observations for this requested source year. This is not a permanent-unavailability claim.'})
                reason='Verified successful source response [] at frozen cutoff; no observations fabricated'
            else:bounds[code].append(year)
        rows.append({'kind':'task','partition':item['task_id'],'dataset':item['dataset'],'status':status,'rows':count,'source_artifact_id':source,'evidence':task.get('export',{}).get('csv_path',''),'reason':reason})
    frozen=json.loads((OUT/'frozen_report_candidates.json').read_text())
    version=sha256(b''.join((ROOT/'src/usda_data/sources'/name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
    for candidate in frozen['candidates']:
        partition=candidate['report_family']+'-'+candidate['report_period'];path=OUT/'report_partitions'/f'{partition}.json'
        record=json.loads(path.read_text()) if path.exists() else {}
        status=record.get('status','pending')
        if record.get('parser_source_hash')!=version:status='stale_parser_check'
        rows.append({'kind':'report','partition':partition,'dataset':candidate['report_family'],'status':status,'rows':record.get('rows'),'source_artifact_id':record.get('source_artifact_id',''),'evidence':str(path.relative_to(ROOT)),'reason':record.get('error','')})
    # Directory omission alone is not proof of nonpublication. Saved official notice
    # explicitly covers the grain and oilseed October 2025 reports, but not WAP.
    notice=OUT/'fas-rescheduled-reports.html'
    from bs4 import BeautifulSoup
    text=BeautifulSoup(notice.read_bytes(),'html.parser').get_text(' ',strip=True)
    for family,label in [('grain-trade','Grains: World Markets and Trade'),('oilseed-trade','Oilseeds: World Markets and Trade'),('world-production','World Agricultural Production')]:
        proven=label+' (October 9 and November 12)' in text
        source_hash=hash_file(notice);evidence_path=str(notice.relative_to(ROOT));reason='Official notice says October data will be included in December report'
        if family=='world-production':
            gap=json.loads((OUT/'resume/october_wap_gap_evidence.json').read_text())
            source_hash=gap['source_artifact_id'];store.artifact(source_hash)
            proven=gap['status']=='source_unavailable' and 'not published in October 2025' in gap['source_text']
            evidence_path='artifacts/acceptance/phase-09/resume/october_wap_gap_evidence.json';reason=gap['source_text']
        rows.append({'kind':'unlisted_report_month','partition':family+'-2025-10','dataset':family,'status':'source_unavailable' if proven else 'unresolved','rows':0,'source_artifact_id':source_hash,'evidence':evidence_path,'reason':reason if proven else 'Directory omission has no family-specific nonpublication evidence yet'})
    wasde_gaps=json.loads((OUT/'wasde_gap_evidence.json').read_text())
    if wasde_gaps['status']!='pass':raise ValueError('Unresolved WASDE source gaps')
    for gap in wasde_gaps['gaps']:
        rows.append({'kind':'unpublished_wasde_month','partition':'wasde-'+gap['period'],'dataset':'wasde','status':gap['status'],'rows':0,'source_artifact_id':gap['source_artifact_id'],'evidence':'artifacts/acceptance/phase-09/wasde_gap_evidence.json','reason':gap['verified_statement']})
    with (OUT/'coverage_manifest.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    counts=Counter(r['status'] for r in rows);unresolved=sum(v for k,v in counts.items() if k not in {'succeeded','source_unavailable'})
    result={'run_id':state['run_id'],'expected':len(rows),'succeeded':counts['succeeded'],'source_unavailable':counts['source_unavailable'],'unresolved':unresolved,'status_counts':dict(counts),'report_parser_source_hash':version,'coverage_boundaries_verified':unresolved==0 and json.loads((OUT/'source_accounting.json').read_text())['status']=='pass' and wasde_gaps['status']=='pass','esr_nonempty_year_bounds':{code:{'earliest':min(years),'latest':max(years)} for code,years in bounds.items()},'empty_source_partitions':len(empty),'historical_vintages_note':'PSD and ESR historical observation years are current-revised API snapshots. Availability of an observation year does not imply archived historical monthly API vintages. Reports retain their own original report vintages.'}
    atomic_write(OUT/'coverage_reconciliation.json',canonical(result));atomic_write(OUT/'empty_source_evidence.json',canonical(empty))
    atomic_write(OUT/'empty_responses_pending_evidence.json',canonical({'status':'resolved_as_verified_empty_responses_at_cutoff','count':len(empty),'evidence':'empty_source_evidence.json','no_permanent_unavailability_inferred':True}))
    print({k:v for k,v in result.items() if k!='esr_nonempty_year_bounds'})
    return int(bool(unresolved))

if __name__=='__main__':raise SystemExit(main())
