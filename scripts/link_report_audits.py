"""Link frozen independent report cells to the exact selected full exports."""
import csv,json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from usda_data.storage import atomic_write,canonical,hash_file

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    active=json.loads((ROOT/'data/manifests/runs/active.json').read_text());state=json.loads((ROOT/'data/manifests/runs'/f'{active["run_id"]}.json').read_text())
    refs=json.loads((ROOT/'tests/fixtures/phase_09/report_audit_references.json').read_text());by_family=defaultdict(list);checks=[]
    for ref in refs:by_family[ref['dataset']].append(ref)
    for family,items in by_family.items():
        task=state['tasks'][family+'-full']
        if task['status']!='succeeded':raise RuntimeError('Required report-family full export is not complete: '+family)
        entry=task['export'];path=ROOT/'data/exports'/entry['csv_path']
        if hash_file(path)!=entry['csv_sha256']:raise RuntimeError('Export hash mismatch')
        by_hash=defaultdict(list);found=defaultdict(list)
        for ref in items:by_hash[ref['sha256']].append(ref)
        with path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                if row['observation_kind']!='report_table':continue
                for ref in by_hash.get(row['source_artifact_id'],[]):
                    dimensions={k:ref[k] for k in ['table_title','row_label','indicator','comparison_label','section_label','period_label','column_commodity'] if k in ref}
                    if row['report_period']==ref['source_report_period'] and int(row['source_page'])==ref['source_page'] and all(row[k]==v for k,v in dimensions.items()):found[ref['reference_id']].append(row)
        for ref in items:
            rows=found[ref['reference_id']];actual=rows[0]['value'] if len(rows)==1 else None
            passed=actual is not None and Decimal(actual)==Decimal(ref['expected_value']) and rows[0]['unit']==ref['expected_unit']
            checks.append({'reference_id':ref['reference_id'],'dataset':family,'status':'pass' if passed else 'fail','matches':len(rows),'expected_value':ref['expected_value'],'actual_value':actual,'export_sha256':entry['csv_sha256'],'export_path':str(path.relative_to(ROOT)),'snapshot_id':rows[0]['snapshot_id'] if len(rows)==1 else None,'source_artifact_id':ref['sha256']})
        print(family,len(items),'checked against complete export',flush=True)
    atomic_write(OUT/'report_export_audit_linkage.json',canonical(checks))
    if any(r['status']!='pass' for r in checks):raise RuntimeError('Independent report cells differ from complete export')
    result=json.loads((OUT/'independent_audit.json').read_text());result['report_export_linkage']='verified';result['report_export_linkage_evidence']='report_export_audit_linkage.json';atomic_write(OUT/'independent_audit.json',canonical(result))
    with (OUT/'source_checks.csv').open(newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    mapping={r['reference_id']:r for r in checks}
    for row in rows:
        if row['reference_id'] in mapping:row['comparison_target']=mapping[row['reference_id']]['export_path']
    with (OUT/'source_checks.csv').open('w',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print('All report references linked:',len(checks))

if __name__=='__main__':main()
