from datetime import date
from decimal import Decimal
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
import httpx
import pandas as pd
import pytest
from usda_data.api import download_wasde, download_dataset
from usda_data.cli import main, export_wasde
from usda_data.errors import FormatError, ValidationError
from usda_data.http import HTTPClient
from usda_data.storage import Store, atomic_write, canonical, sha256
from usda_data.sources.wasde import COLUMNS, DIMENSIONS, OPTIONAL, SCHEMA, discover, iter_csv_partitions, iter_download, reconcile_xml, xml_footnotes

ROOT=Path(__file__).resolve().parents[2]
OUT=None
FIX=ROOT/'test/fixtures/phase_02'
REFERENCES=json.loads((FIX/'references.json').read_text())
CATALOG=json.loads((FIX/'catalog.json').read_text())
EXPECTED=json.loads((FIX/'expected_coverage.json').read_text())


def load(role, start=None, end=None):
    entry=next(e for e in CATALOG if e['role']==role)
    path=ROOT/entry['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    meta=json.loads((ROOT/entry['acquisition_record']).read_text())
    receipt={'source_artifact_id':entry['sha256'],'retrieved_at_utc':meta['checked_at_utc']}
    day=next(r['source_release_date'] for r in REFERENCES if r['role']==role)
    accounting={}
    parts=list(iter_csv_partitions(path,receipt,start=start or day,end=end or day,accounting=accounting))
    return pd.concat([f for _,f in parts],ignore_index=True) if parts else SCHEMA.frame([]),accounting


def seed(store, role='recent', with_xml=False):
    entry=next(e for e in CATALOG if e['role']==role)
    receipt=store.raw((ROOT/entry['path']).read_bytes(),metadata={'url':entry['url']})
    url=entry['url']
    links=[{'url':url,'format':'csv','kind':'history'}]
    atomic_write(store.root/'manifests/wasde/urls'/f'{sha256(url.encode())}.json',canonical(receipt))
    if with_xml:
        cat=json.loads((ROOT/'test/fixtures/catalog.json').read_text())
        item=next(e for e in cat['artifacts'] if e['artifact_id']=='wasde-development')
        receipt=store.raw((ROOT/item['path']).read_bytes(),metadata={'url':item['url']})
        atomic_write(store.root/'manifests/wasde/urls'/f'{sha256(item["url"].encode())}.json',canonical(receipt))
        links.append({'url':item['url'],'format':'xml','kind':'current'})
    atomic_write(store.root/'manifests/wasde/discovery.json',canonical({'links':links}))


@pytest.mark.acceptance('P02-A2')
def test_independent_source_observations():
    checks=[]
    for role in ['early','transition','recent']:
        frame,_=load(role)
        refs=[r for r in REFERENCES if r['role']==role]
        assert len(refs)>=10
        for ref in refs:
            selected=frame
            for key,value in ref['dimensions'].items():
                selected=selected[selected[key]==(value or OPTIONAL.get(key,''))]
            assert len(selected)==1,ref['reference_id']
            actual=selected.iloc[0]
            assert actual['Value']==Decimal(ref['expected_value'])
            assert actual['Unit']==ref['expected_unit']
            assert actual['source_release_date'].isoformat()==ref['source_release_date']
            checks.append({'reference_id':ref['reference_id'],'source_url':ref['source_url'],'artifact_sha256':ref['sha256'],'locator':str(ref['locator']),'expected_value':ref['expected_value'],'actual_value':str(actual['Value']),'unit':actual['Unit'],'status':'pass','tolerance':'0'})
    assert len(checks)>=30
    out=OUT/'source_checks.csv'
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(checks[0]));writer.writeheader();writer.writerows(checks)


@pytest.mark.acceptance('P02-A3')
def test_cross_format_overlap_and_conflict_blocking(tmp_path):
    frame,_=load('recent')
    xml=(ROOT/'test/fixtures/raw/wasde-development.xml').read_bytes()
    checks,accounting=reconcile_xml(frame,xml)
    assert len(checks)==360 and all(c['status']=='pass' for c in checks)
    changed=frame.copy()
    mask=(changed['ReportTitle']=='World and U.S. Supply and Use for Grains')&(changed['Commodity']=='Total Grains')&(changed['Region']=='World')&(changed['MarketYear']=='2024/25')&(changed['Attribute']=='Output')
    changed.loc[mask,'Value']=Decimal('999')
    conflicts,_=reconcile_xml(changed,xml)
    assert sum(c['status']=='conflict' for c in conflicts)==1
    store=Store(tmp_path);seed(store,with_xml=True)
    actual=download_wasde('2026-11-10','2026-11-10',data_dir=tmp_path)
    assert len(actual)==5054
    old=store.latest('wasde','2026-11-10')
    # Change the source XML in a new raw artifact and cache receipt; never alter a fixture.
    corrupt=xml.replace(b'cell_value1="2858.10"',b'cell_value1="2859.10"',1)
    xml_url='https://www.usda.gov/oce/commodity/wasde/wasde1126.xml'
    receipt=store.raw(corrupt,metadata={'url':xml_url})
    atomic_write(store.root/'manifests/wasde/urls'/f'{sha256(xml_url.encode())}.json',canonical(receipt))
    with pytest.raises(ValidationError,match='conflict'):
        download_wasde('2026-11-10','2026-11-10',data_dir=tmp_path)
    assert store.latest('wasde','2026-11-10')==old
    report={'comparisons':checks,'accounting':accounting,'synthetic_conflict_rejected':True}
    (OUT/'overlap.json').write_text(json.dumps(report,indent=2)+'\n')


@pytest.mark.acceptance('P02-A4')
def test_report_vintages_remain_distinct():
    a,_=load('transition');b,_=load('recent')
    together=SCHEMA.validate(pd.concat([a,b],ignore_index=True))
    common=together[(together['Commodity']=='Corn')&(together['Region']=='United States')&(together['MarketYear']=='2025/26')&(together['Attribute']=='Production')]
    assert common['source_release_date'].nunique()==2
    assert len(together)==len(a)+len(b)


@pytest.mark.acceptance('P02-A5')
def test_complete_csv_table_cell_accounting():
    summaries={}
    for role in ['early','transition','recent']:
        frame,accounting=load(role)
        assert len(frame)==EXPECTED[role]['rows']==accounting['mapped_rows']
        assert accounting['tables']==EXPECTED[role]['tables']
        assert accounting['input_rows']==accounting['mapped_rows']+accounting['excluded_outside_bounds']
        assert accounting['quarantined_rows']==0
        assert frame['Value'].isna().sum()==EXPECTED[role]['missing_values']
        assert all(row.value_status=='missing' for row in frame[frame['Value'].isna()].itertuples())
        assert (frame['Value']==Decimal('0')).any()
        summaries[role]=accounting
    # Every current XML title resolves to a current CSV table family, including livestock and reliability.
    tables=xml_footnotes((ROOT/'test/fixtures/raw/wasde-development.xml').read_bytes())
    import re
    def norm(title):
        title=re.sub(r'\d+/','',title).replace(', Continued','').replace("(Cont'd.)",'').replace('(Continued)','')
        return ' '.join(title.split())
    csv_titles={norm(t) for t in EXPECTED['recent']['tables']}
    mapping=[]
    for table in tables:
        for title in table['titles'].values():
            assert norm(title) in csv_titles,(table['source_table'],title)
            mapping.append({'xml_table':table['source_table'],'xml_title':title,'csv_table':norm(title),'status':'mapped_current_monthly_csv','footnotes':table['footnotes']})
    assert {r['csv_table'] for r in mapping}==csv_titles
    (OUT/'table_coverage.json').write_text(json.dumps({'accounting':summaries,'xml_to_csv':mapping},indent=2)+'\n')


@pytest.mark.acceptance('P02-A5')
def test_invalid_layout_missing_dimensions_and_markers(tmp_path):
    raw=(FIX/'current.csv').read_text()
    receipt={'source_artifact_id':'a'*64,'retrieved_at_utc':'2026-11-15T00:00:00+00:00'}
    for mutation in [raw.replace('WasdeNumber','Unknown',1),raw.replace('Beginning Stocks','',1)]:
        path=tmp_path/'bad.csv';path.write_text(mutation)
        with pytest.raises((ValidationError,FormatError)):
            list(iter_csv_partitions(path,receipt,start='2026-11-10',end='2026-11-10'))
    # Real source defect remains visible; it cannot silently lose seven Pork reliability rows.
    accounting={}
    with pytest.raises(ValidationError,match='Attribute'):
        list(iter_csv_partitions(FIX/'early-cdn.zip',receipt,start='2011-05-11',end='2011-05-11',accounting=accounting))
    assert accounting['quarantined_rows']==1


@pytest.mark.acceptance('P02-A6')
def test_public_cli_exact_bounds_and_csv(tmp_path):
    store=Store(tmp_path/'data');seed(store)
    frame=download_wasde('2026-11-10','2026-11-10',data_dir=store.root)
    assert len(frame)==5054
    assert len(download_wasde('2026-11-01','2026-11-09',data_dir=store.root))==0
    assert len(download_wasde('2026-11-11','2026-11-30',data_dir=store.root))==0
    assert main(['fetch','--dataset','wasde','--start','2026-11-10','--end','2026-11-10','--data-dir',str(store.root),'--output-dir',str(tmp_path/'exports')])==0
    manifest=json.loads((tmp_path/'exports/wasde.latest.json').read_text())
    reloaded=SCHEMA.read_csv(tmp_path/'exports'/manifest['csv_path'])
    pd.testing.assert_frame_equal(frame,reloaded)
    pd.testing.assert_frame_equal(frame,download_dataset('wasde',start='2026-11-10',end='2026-11-10',data_dir=store.root))
    assert len(list((store.root/'normalized/wasde/2026-11-10').iterdir()))==1


@pytest.mark.acceptance('P02-A7')
def test_holdout_first_run():
    output=OUT/'holdout_first_run.json'
    result={'artifact_role':'holdout','schema_layout':'16-field official monthly CSV; October 2026 XML summary families','expected_reference_count':12,'status':'running'}
    try:
        frame,accounting=load('holdout')
        for ref in [r for r in REFERENCES if r['role']=='holdout']:
            selected=frame
            for key,value in ref['dimensions'].items():
                selected=selected[selected[key]==(value or OPTIONAL.get(key,''))]
            assert len(selected)==1
            assert selected.iloc[0]['Value']==Decimal(ref['expected_value'])
        checks,_=reconcile_xml(frame,(ROOT/'test/fixtures/raw/wasde-holdout.xml').read_bytes())
        assert len(checks)>=10 and all(c['status']=='pass' for c in checks)
        result.update(status='pass',rows=len(frame),overlap_checks=len(checks),accounting=accounting)
    except Exception:
        result['status']='fail';raise
    finally:
        if not output.exists():
            output.write_text(json.dumps(result,indent=2)+'\n')


@pytest.mark.live
@pytest.mark.acceptance('P02-A1')
def test_live_discovery_current_artifact(tmp_path):
    evidence=OUT/'live';store=Store(evidence/'data')
    with HTTPClient() as client:
        discovered=discover(client,store)
        links=[x for x in discovered['links'] if x['format']=='csv']
        current=max(links,key=lambda x:x['url'].split('report-data-')[1])
        body,metadata=client.get(current['url'],expected='csv')
        receipt=store.raw(body,metadata=metadata)
        path=store.artifact(receipt['source_artifact_id'])
        frames=list(iter_csv_partitions(path,receipt,start='2010-01-01',end='2100-12-31'))
        assert len(frames)==1
        day,frame=frames[0]
        assert receipt['source_artifact_id']==sha256(body)
        assert frame['source_release_date'].unique().tolist()==[day]
        assert len(frame)>0
        atomic_write(evidence/'current_artifact.json',canonical({'receipt':receipt,'report_date':day.isoformat(),'rows':len(frame),'discovery':discovered}))

@pytest.mark.acceptance('P02-A5')
def test_exact_source_dimension_repairs_and_conflict_provenance():
    from usda_data.sources.wasde import REPAIRS
    frame, accounting = load('early', start='2011-05-11', end='2011-05-11')
    repaired = frame[frame['source_dimension_repair'] != '']
    assert len(repaired) == 7
    assert set(repaired['Attribute']) == {'Production'}
    assert set(repaired[repaired['ReliabilityProjection'].isin(['average','smallest','largest'])]['Unit']) == {'Million Pounds'}
    assert json.loads(repaired.iloc[0]['source_original_dimensions'])['Attribute'] == ''
    conflict = repaired[repaired['ReliabilityProjection'] == 'root_mean_square_error'].iloc[0]
    assert conflict['Value'] == Decimal('3.50')
    assert json.loads(conflict['source_conflict'])['pdf_value'] == '3.4'
    assert accounting['quarantined_rows'] == 0
    pdf=ROOT/'test/fixtures/phase_02/original-wasde-05-11-2011.pdf'
    assert sha256(pdf.read_bytes()) == REPAIRS['pdf_sha256']
    (OUT/'source_dimension_repairs.json').write_text(json.dumps(REPAIRS, indent=2)+'\n')

@pytest.mark.acceptance('P02-A5')
def test_discovery_preserves_official_fallback_evidence(tmp_path):
    from usda_data.sources.wasde import LANDING, HISTORY
    seen=[]
    def handler(request):
        seen.append(str(request.url))
        if str(request.url)==HISTORY:
            return httpx.Response(403)
        filename='current.html' if str(request.url)==LANDING else 'history.html'
        return httpx.Response(200,content=(ROOT/'test/fixtures/discovery/phase-02/discovery'/filename).read_bytes())
    with HTTPClient(transport=httpx.MockTransport(handler)) as client:
        manifest=discover(client,Store(tmp_path))
    assert len(seen)==3 and any(x['format']=='zip' for x in manifest['links'])
    receipts=[json.loads(p.read_text()) for p in (tmp_path/'manifests/acquisitions').glob('*.json')]
    assert any(r.get('original_url')==HISTORY for r in receipts)
