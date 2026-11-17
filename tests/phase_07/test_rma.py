from decimal import Decimal
from pathlib import Path
import csv,io,json,zipfile
import pandas as pd
import pytest
from usda_data.sources import rma_sob as rma
from usda_data.storage import Store,atomic_write,canonical,sha256,hash_file
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.api import download_rma_sob,download_dataset
from usda_data.cli import main
from usda_data.errors import FormatError,ValidationError,ConfigurationError

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/acceptance/phase-07';FIX=ROOT/'tests/fixtures/phase_07'
INV=json.loads((FIX/'inventory.json').read_text());REFS=json.loads((FIX/'references.json').read_text());TOTALS=json.loads((FIX/'subtotals.json').read_text())


def artifact(role):
    item=next(i for i in INV if i['role']==role);p=ROOT/item['artifact'];a=json.loads(Path(str(p)+'.acquisition.json').read_text());assert hash_file(p)==item['sha256']
    return p,{'source_artifact_id':a['sha256'],'retrieved_at_utc':a['checked_at_utc']},item


@pytest.fixture(scope='module')
def normalized(tmp_path_factory):
    root=tmp_path_factory.mktemp('rma-annual');result={}
    for role,year in [('development',2025),('holdout',2010)]:
        p,receipt,item=artifact(role);store=Store(root);raw=store.raw(p.read_bytes(),metadata={'url':'https://example.test/pinned-rma-fixture'})
        # Use the same source receipt time for reproducible comparison with direct parsing.
        acc={};first=OUT/'holdout_first_run.json';status={'status':'running','artifact':item['artifact'],'source_sha256':item['sha256']}
        try:
            manifest=store.publish_stream('rma-sob',str(year),rma.iter_parse(p,receipt,year,accounting=acc),rma.SCHEMA,[raw['source_artifact_id']],parser_version=rma.PARSER_VERSION,configuration={'test_layout':'28-field'})
            assert manifest['rows']==item['rows'] and acc['mapped_rows']==item['rows']
            status.update(status='pass',rows=manifest['rows'],layout='28-field 1989-forward',accounting=acc)
        except Exception:status['status']='fail';raise
        finally:
            if role=='holdout' and not first.exists():first.write_text(json.dumps(status,indent=2)+'\n')
        result[role]={'manifest':manifest,'store':store,'accounting':acc,'receipt':receipt}
    return result


def chunks(normalized,role,size=5000):
    r=normalized[role]
    return rma.SCHEMA.read_csv_chunks(r['store'].root/r['manifest']['csv_path'],size)


@pytest.mark.acceptance('P07-A2')
def test_independent_numeric_fields(normalized):
    checks=[]
    for role in ['development','holdout']:
        refs=[r for r in REFS if r['role']==role];lines={r['locator']['line'] for r in refs};found={}
        for frame in chunks(normalized,role):
            for row in frame[frame['source_line'].isin(lines)].to_dict('records'):found[row['source_line']]=row
        for ref in refs:
            row=found[ref['locator']['line']];expected=Decimal(ref['expected_value']) if ref['expected_value'] else None
            assert row[ref['field']]==expected
            assert [str(row[k]) for k in rma.KEYS[:11]]==ref['grouping_fields'][:11]
            assert row['coverage_level']==Decimal(ref['grouping_fields'][11]) and row['quantity_type']==ref['grouping_fields'][12]
            checks.append({'reference_id':ref['reference_id'],'source_url':ref['source_url'],'sha256':ref['sha256'],'member':ref['member'],'locator':json.dumps(ref['locator']),'expected_value':ref['expected_value'],'actual_value':str(row[ref['field']]),'unit':ref['unit'],'status':'pass','tolerance':'0'})
    assert len(checks)>=30
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


@pytest.mark.acceptance('P07-A3')
def test_codes_and_nonacre_types(normalized):
    types=set()
    for role in ['development','holdout']:
        for frame in chunks(normalized,role):
            assert frame['state_code'].map(len).eq(2).all() and frame['county_code'].map(len).eq(3).all() and frame['commodity_code'].map(len).eq(4).all()
            types.update(frame['quantity_type'])
    assert {'Acres','Pounds','Tons','Trees','Colonies'}<=types
    (OUT/'quantity_types.json').write_text(json.dumps({'observed_types':sorted(types),'rule':'Net reported quantity always retains its source quantity_type; endorsed_companion_acres remains a distinct acreage field'},indent=2)+'\n')


@pytest.mark.acceptance('P07-A4')
def test_row_accounting_and_cross_chunk_keys(normalized,tmp_path):
    for role in ['development','holdout']:
        item=next(x for x in INV if x['role']==role);r=normalized[role]
        assert r['manifest']['rows']==r['accounting']['input_rows']==r['accounting']['mapped_rows']==item['rows']
        assert r['accounting']['quarantined_rows']==0
        assert r['accounting']['quantity_types']==item['quantity_types']
    frame=next(chunks(normalized,'development')).iloc[:1]
    store=Store(tmp_path);receipt=store.raw(b'synthetic duplicate test',metadata={})
    with pytest.raises(ValidationError,match='across streaming chunks'):
        store.publish_stream('rma-sob','2025',iter([frame,frame]),rma.SCHEMA,[receipt['source_artifact_id']],parser_version='synthetic-duplicate',configuration={})
    assert store.latest('rma-sob','2025') is None
    changed=frame.copy();changed.loc[changed.index[0],'coverage_level']=frame.iloc[0]['coverage_level'].normalize()
    with pytest.raises(ValidationError,match='across streaming chunks'):
        store.publish_stream('rma-sob','2025',[frame,changed],rma.SCHEMA,[receipt['source_artifact_id']],parser_version='synthetic-scale',configuration={})


@pytest.mark.acceptance('P07-A5')
def test_disjoint_independent_subtotals(normalized):
    results=[]
    metrics=['net_reported_quantity','liability_amount','total_premium','indemnity_amount']
    for expected in TOTALS:
        role='development' if expected['commodity_year']=='2025' else 'holdout';actual={k:0 for k in metrics};count=0;missing=0
        for frame in chunks(normalized,role):
            subset=frame[(frame['state_code']==expected['state_code'])&(~frame['county_code'].isin(expected['county_exclusions']))&(frame['quantity_type']==expected['quantity_type'])]
            complete=subset.dropna(subset=metrics);missing+=len(subset)-len(complete);count+=len(complete)
            for k in metrics:actual[k]+=sum(complete[k],0)
        assert count==expected['rows'] and missing==expected.get('excluded_missing_rows',0)
        for k in metrics:assert actual[k]==expected[k]
        results.append({'year':expected['commodity_year'],'state_code':expected['state_code'],'quantity_type':expected['quantity_type'],'rows':count,'excluded_missing_rows':missing,**actual,'status':'pass'})
    assert len(results)>=2
    (OUT/'subtotal_checks.json').write_text(json.dumps(results,indent=2)+'\n')


@pytest.mark.acceptance('P07-A6')
def test_holdout_signed_adjustments_missing_and_bad_layout(normalized,tmp_path):
    assert json.loads((OUT/'holdout_first_run.json').read_text())['status']=='pass'
    negative=[];missing=0
    for frame in chunks(normalized,'development'):
        negative.extend(frame[frame['indemnity_amount']<0].to_dict('records'));missing+=frame['net_reported_quantity'].isna().sum()
    assert negative and negative[0]['loss_ratio']<0 and missing==448
    p,receipt,_=artifact('development')
    with zipfile.ZipFile(p) as z:row=z.read(z.namelist()[0]).splitlines()[0].decode().split('|')
    for member,line in [('sobcov_2025.txt','|'.join(row[:-1])),('unknown.txt','|'.join(row))]:
        path=tmp_path/'bad.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr(member,line+'\n')
        with pytest.raises(FormatError):list(rma.iter_parse(path,receipt,2025))
    with pytest.raises(ConfigurationError):rma.years_option([1988])
    # Failure after writing output but before selecting latest retains the old version.
    store=Store(tmp_path/'store');raw=store.raw(b'synthetic',metadata={});frame=next(chunks(normalized,'development')).iloc[:2]
    before=store.publish_stream('rma-sob','2025',[frame],rma.SCHEMA,[raw['source_artifact_id']],parser_version='A',configuration={})
    def fail():raise OSError('Injected publication interruption')
    with pytest.raises(OSError):store.publish_stream('rma-sob','2025',[frame],rma.SCHEMA,[raw['source_artifact_id']],parser_version='B',configuration={},before_publish=fail)
    assert store.latest('rma-sob','2025')==before


@pytest.mark.acceptance('P07-A7')
def test_chunk_size_and_public_cli_equality(normalized,tmp_path):
    # A deliberately smaller bound produces the same complete annual byte stream.
    r=normalized['development'];p,receipt,_=artifact('development');old=r['manifest']
    small=r['store'].publish_stream('rma-sob','2025',rma.iter_parse(p,receipt,2025,chunk_size=997),rma.SCHEMA,[receipt['source_artifact_id']],parser_version=rma.PARSER_VERSION,configuration={'test_layout':'28-field'})
    assert old==small
    # Public/CLI path uses a real complete single-year official source (not a fake subset).
    store=Store(tmp_path/'data');a=json.loads(Path(str(p)+'.acquisition.json').read_text());raw=store.raw(p.read_bytes(),metadata={'url':a['url']})
    layout=ROOT/'tests/fixtures/raw/rma-layout.pdf';lr=store.raw(layout.read_bytes(),metadata={})
    atomic_write(store.root/'manifests/rma-sob/urls'/f'{sha256(a["url"].encode())}.json',canonical(raw))
    atomic_write(store.root/'manifests/rma-sob/discovery.json',canonical({'years':{'2025':a['url']},'layout_artifact_id':lr['source_artifact_id'],'unsupported_history':{'period':'1948-1988'}}))
    frame=download_rma_sob([2025],data_dir=store.root)
    assert len(frame)==155676
    assert main(['fetch','--dataset','rma-sob','--commodity-years','2025','--chunk-size','997','--data-dir',str(store.root),'--output-dir',str(tmp_path/'exports')])==0
    manifest=json.loads((tmp_path/'exports/rma-sob.latest.json').read_text());reloaded=rma.SCHEMA.read_csv(tmp_path/'exports'/manifest['csv_path'])
    pd.testing.assert_frame_equal(frame,reloaded)
    assert manifest['rows']==old['rows'] and len(manifest['snapshot_ids'])==1


@pytest.mark.live
@pytest.mark.acceptance('P07-A1')
def test_live_discovery_zip_and_layout():
    store=Store(OUT/'live/data')
    with HTTPClient(HTTPConfig(trust_environment=False)) as client:
        inventory=rma.discover(client,store,refresh=True)
        assert '2025' in inventory['years'] and inventory['supported_start_year']==1989
        assert inventory['unsupported_history']['period']=='1948-1988'
        path,receipt=rma.fetch(client,store,inventory['years']['2025'],'zip',refresh=True)
        # Read/validate the entire actual data member, not merely a ZIP magic prefix.
        acc={};rows=0
        for frame in rma.iter_parse(path,receipt,2025,chunk_size=5000,accounting=acc):rows+=len(frame)
        assert rows>0 and rows==acc['input_rows'] and acc['quarantined_rows']==0
        atomic_write(OUT/'live/checks.json',canonical({'inventory':inventory,'receipt':receipt,'accounting':acc,'rows':rows,'status':'pass'}))
