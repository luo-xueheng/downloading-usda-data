"""Export complete attachment/table coverage for the exact completed report parser version."""
from pathlib import Path
from collections import defaultdict
import csv,json
from usda_data.storage import canonical,atomic_write,hash_file,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    summary=json.loads((OUT/'report_backfill_summary.json').read_text())
    version=sha256(b''.join((ROOT/'src/usda_data/sources'/name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
    if summary['failed'] or summary['parser_source_hash']!=version:raise RuntimeError('Report coverage has failed or stale parser checks')
    layouts=defaultdict(list);tables=[];attachments=[]
    for path in sorted((OUT/'report_partitions').glob('*.json')):
        record=json.loads(path.read_text())
        if record['parser_source_hash']!=version or record['status'] not in {'succeeded','source_unavailable'}:raise RuntimeError('Unresolved report partition')
        if hash_file(ROOT/'data'/record['attachment_path'])!=record['source_artifact_id']:raise RuntimeError('Attachment hash mismatch')
        if hash_file(ROOT/'data'/record['csv_path'])!=record['csv_sha256']:raise RuntimeError('Normalized report hash mismatch')
        coverage=json.loads((ROOT/'data'/record['coverage_path']).read_text())
        if coverage['input_cells']!=record['input_cells'] or coverage['unique_cells']!=record['rows']:raise RuntimeError('Report source-cell accounting mismatch')
        if coverage['input_cells']!=coverage['unique_cells']+coverage['duplicate_cells']:raise RuntimeError('Unexplained report cell loss')
        attachments.append({k:record.get(k) for k in ['family','report_period','status','source_artifact_id','url','resolved_url','attachment_path','rows','input_cells','snapshot_id','csv_sha256']})
        for table in coverage['tables']:
            entry={'family':record['family'],'report_period':record['report_period'],'table_title':table['table_title'],'source_page':table['source_page'],'layout':table['layout'],'required':True,'status':'separate_extraction','input_cells':table['input_cells'],'source_artifact_id':record['source_artifact_id'],'evidence_path':record['coverage_path']}
            if not entry['input_cells']:raise RuntimeError('Available table has no accounted cells')
            tables.append(entry);layouts[(entry['family'],entry['layout'])].append(entry)
        for gap in coverage.get('source_table_gaps',[]):
            tables.append({'family':record['family'],'report_period':record['report_period'],'table_title':gap['missing_table_title'],'source_page':'not_present','layout':'source_missing_table','required':True,'status':'source_unavailable','input_cells':0,'source_artifact_id':record['source_artifact_id'],'evidence_path':'src/usda_data/sources/report_source_gaps.json'})
        if coverage.get('source_unavailable'):
            tables.append({'family':record['family'],'report_period':record['report_period'],'table_title':'Report not published per original notice','source_page':1,'layout':'nonpublication_notice','required':True,'status':'source_unavailable','input_cells':0,'source_artifact_id':record['source_artifact_id'],'evidence_path':record['coverage_path']})
    for name,rows in [('report_coverage.csv',tables),('report_attachment_inventory.csv',attachments)]:
        with (OUT/name).open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    inventory=[{'family':family,'layout':layout,'table_instances':len(rows),'earliest':min(r['report_period'] for r in rows),'latest':max(r['report_period'] for r in rows),'example':rows[0]} for (family,layout),rows in sorted(layouts.items())]
    atomic_write(OUT/'report_layout_inventory.json',canonical({'parser_source_hash':version,'attachments':len(attachments),'required_table_instances':len(tables),'unresolved_available_tables':0,'layouts':inventory}))
    print({'attachments':len(attachments),'tables':len(tables),'layout_families':len(layouts),'unresolved_available_tables':0})

if __name__=='__main__':main()
