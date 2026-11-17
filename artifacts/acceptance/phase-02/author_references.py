"""Independent standard-library source reading, selected before adapter implementation.
No usda_data imports. Select fixed categories/positions, retain all lexical fields.
"""
import csv, io, json, hashlib, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
selections=[('early','tests/fixtures/phase_02/early-cdn.zip'),('transition','tests/fixtures/phase_02/transition.csv'),('recent','tests/fixtures/phase_02/current.csv'),('holdout','tests/fixtures/phase_02/holdout.csv')]
references=[];catalog=[]
for role,name in selections:
    raw=(ROOT/name).read_bytes();sha=hashlib.sha256(raw).hexdigest()
    acquisition=json.loads((ROOT/(name+'.acquisition.json')).read_text())
    if name.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            member=z.namelist()[0];stream=io.TextIOWrapper(z.open(member),encoding='utf-8-sig',newline='');rows=list(csv.DictReader(stream))
    else:
        member=None;rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    first_date=rows[0]['ReleaseDate']; selected=[]
    for substring in ['Mexico Sugar','U.S. Wheat Supply','World Corn','U.S. Meats','U.S. Dairy','Reliability of United States']:
        matches=[(i,r) for i,r in enumerate(rows,2) if substring in r['ReportTitle'] and r['ReleaseDate']==first_date and r['Value']]
        selected.extend(matches[:2])
    assert len(selected)>=12
    for line,row in selected:
        references.append({'reference_id':f'{role}-{line}','role':role,'source_url':acquisition['url'],'artifact_path':name,'sha256':sha,'zip_member':member,'locator':{'csv_record_including_header':line},'source_release_date':row['ReleaseDate'],'dimensions':{k:v for k,v in row.items() if k!='Value'},'expected_value':row['Value'],'expected_unit':row['Unit'],'creation_method':'Independent stdlib csv reader at fixed table/category positions, before production adapter; full source dimensions retained','tolerance':'0'})
    catalog.append({'role':role,'path':name,'sha256':sha,'url':acquisition['url'],'acquisition_record':name+'.acquisition.json','zip_member':member,'selected_before_adapter':True,'first_adapter_run':'not_run'})
output=ROOT/'tests/fixtures/phase_02'
(output/'references.json').write_text(json.dumps(references,indent=2)+'\n')
(output/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
print('Frozen independent references:',len(references))
print('Early releases:',len({r['source_release_date'] for r in references if r['role']=='early'}))
