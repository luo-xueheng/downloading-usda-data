from datetime import date
from decimal import Decimal
from pathlib import Path
import csv
import json
import httpx
import pandas as pd
import pytest
from usda_data.sources import fas_esr as esr
from usda_data.sources import fas_common as fas
from usda_data.storage import Store,atomic_write,canonical,sha256
from usda_data.http import HTTPClient
from usda_data.api import download_export_sales,download_dataset
from usda_data.cli import main
from usda_data.errors import AuthenticationError,FormatError,ValidationError

ROOT=Path(__file__).resolve().parents[2];FIX=ROOT/'test/fixtures/phase_04';OUT=ROOT/'.cache/test-output/phase-04'
CAT=json.loads((FIX/'catalog.json').read_text());REFS=json.loads((FIX/'references.json').read_text())
DICT={n:json.loads((FIX/(n+'.json')).read_text()) for n in esr.DICTIONARIES}


def payload(id):
    p=FIX/(id+'.json');a=json.loads(Path(str(p)+'.acquisition.json').read_text());body=p.read_bytes()
    assert sha256(body)==a['sha256'] and a['status']==200
    return body,{'source_artifact_id':a['sha256'],'retrieved_at_utc':a['checked_at_utc']}


def load(code,year):
    id=f'esr-{code}-{year}';body,r=payload(id);expected=next(e['expected_records'] for e in CAT if e['id']==id)
    return esr.parse(body,DICT,r,commodity=code,market_year=year,expected_records=expected)


def seed(store,ids):
    endpoints={n:'/api/esr/'+n for n in esr.DICTIONARIES}
    endpoints.update({id:esr.path_for(*id.split('-')[1:]) for id in ids})
    for id,path in endpoints.items():
        body,_=payload(id);url=fas.BASE+path;r=store.raw(body,metadata={'url':url})
        atomic_write(store.root/'manifests/fas/urls'/f'{sha256(url.encode())}.json',canonical(r))


@pytest.mark.acceptance('P04-A2')
def test_independent_values():
    checks=[];frames={}
    for ref in REFS:
        if ref['role']=='holdout':continue
        dims=ref['dimensions'];code=dims['commodityCode'];year=int(ref['market_year']);key=(code,year)
        if key not in frames:frames[key]=load(code,year)
        frame=frames[key]
        selected=frame[(frame['countryCode']==str(dims['countryCode']))&(frame['weekEndingDate']==date.fromisoformat(dims['weekEndingDate'][:10]))]
        assert len(selected)==1
        row=selected.iloc[0];field=ref['locator']['field']
        assert row[field]==Decimal(ref['expected_value'])
        assert row['commodityCode']==str(code) and row['marketYear']==str(year) and row['unitId']==str(dims['unitId']) and row['unit']==ref['unit']
        assert sha256((ROOT/ref['artifact']).read_bytes())==ref['sha256']
        checks.append({'reference_id':ref['reference_id'],'artifact_sha256':ref['sha256'],'source_url':fas.BASE+ref['source_url'],'locator':json.dumps(ref['locator']),'commodity':code,'country':dims['countryCode'],'market_year':year,'expected_value':ref['expected_value'],'actual_value':str(row[field]),'unit':row['unit'],'status':'pass','tolerance':'0'})
    assert len(checks)>=30 and len({r['commodity'] for r in checks})>=3 and len({r['country'] for r in checks})>=2 and len({r['market_year'] for r in checks})>=2
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


@pytest.mark.acceptance('P04-A3')
def test_boundary_week_keeps_both_source_years():
    a=load(107,2025);b=load(107,2026)
    assert a['weekEndingDate'].max()==b['weekEndingDate'].min()==date(2025,6,5)
    together=esr.SCHEMA.validate(pd.concat([a,b],ignore_index=True))
    boundary=together[(together['countryCode']=='1220')&(together['weekEndingDate']==date(2025,6,5))]
    assert set(boundary['marketYear'])=={'2025','2026'}
    assert boundary['source_release_date'].isna().all() and boundary['source_release_at_utc'].isna().all()
    assert set(boundary['release_time_precision'])=={'unknown'}
    assert set(boundary['commodity_release_timestamp_raw'])=={next(r['releaseTimeStamp'] for r in DICT['datareleasedates'] if r['commodityCode']==107)}


@pytest.mark.acceptance('P04-A4')
def test_real_and_synthetic_cancellations_preserved():
    for code in [107,401,801]:assert (load(code,2026)['currentMYNetSales']<0).any()
    body,receipt=payload('esr-401-2026');rows=json.loads(body)[:1]
    rows[0]['currentMYNetSales']=-123;rows[0]['nextMYNetSales']=-456
    frame=esr.parse(json.dumps(rows).encode(),DICT,receipt,commodity=401,market_year=2026)
    assert frame.iloc[0]['currentMYNetSales']==Decimal(-123) and frame.iloc[0]['nextMYNetSales']==Decimal(-456)


@pytest.mark.acceptance('P04-A5')
def test_full_record_counts_and_unknown_or_truncated_failures():
    for entry in CAT:
        if entry['role']=='holdout':continue
        code,year=map(int,entry['id'].split('-')[1:]);assert len(load(code,year))==entry['expected_records']
    body,receipt=payload('esr-401-2026');raw=json.loads(body)
    invalid=[]
    unknown=json.loads(body);unknown[0]['countryCode']=999999;invalid.append(json.dumps(unknown).encode())
    fields=json.loads(body);fields[0]['unexpected']=1;invalid.append(json.dumps(fields).encode())
    invalid.extend([body[:-10],json.dumps({'data':raw,'next':'page2'}).encode(),json.dumps(raw[:1]).encode()])
    for wrong in invalid:
        with pytest.raises((FormatError,ValidationError)):
            esr.parse(wrong,DICT,receipt,commodity=401,market_year=2026,expected_records=len(raw))
    # Country-specific endpoints independently reproduce the exact subsets, without a page cap.
    comparisons=[]
    for code,country,year in [(401,1220,2026),(801,2010,2025)]:
        all_rows=json.loads(payload(f'esr-{code}-{year}')[0]);single=json.loads(payload(f'country-{code}-{country}-{year}')[0])
        subset=[r for r in all_rows if r['countryCode']==country]
        assert sorted(subset,key=lambda r:r['weekEndingDate'])==sorted(single,key=lambda r:r['weekEndingDate'])
        comparisons.append({'commodity':code,'country':country,'market_year':year,'all_country_subset':len(subset),'independent_country_rows':len(single),'status':'pass'})
    (OUT/'completeness_checks.json').write_text(json.dumps(comparisons,indent=2)+'\n')


@pytest.mark.acceptance('P04-A6')
def test_holdout_first_run_and_python_cli(tmp_path):
    first=OUT/'holdout_first_run.json';result={'status':'running','artifact':'esr-701-2026','selected_before_adapter':True}
    try:
        frame=load(701,2026)
        for ref in [r for r in REFS if r['role']=='holdout']:
            dims=ref['dimensions'];row=frame[(frame['countryCode']==str(dims['countryCode']))&(frame['weekEndingDate']==date.fromisoformat(dims['weekEndingDate'][:10]))]
            assert len(row)==1 and row.iloc[0][ref['locator']['field']]==Decimal(ref['expected_value'])
        store=Store(tmp_path/'data');seed(store,['esr-701-2026'])
        public=download_export_sales(['701'],[2026],data_dir=store.root)
        assert len(public)==len(frame)
        assert main(['fetch','--dataset','export-sales','--commodities','701','--market-years','2026','--data-dir',str(store.root),'--output-dir',str(tmp_path/'exports')])==0
        manifest=json.loads((tmp_path/'exports/export-sales.latest.json').read_text())
        pd.testing.assert_frame_equal(public,esr.SCHEMA.read_csv(tmp_path/'exports'/manifest['csv_path']))
        pd.testing.assert_frame_equal(public,download_dataset('export-sales',commodities=['701'],market_years=[2026],data_dir=store.root))
        result.update(status='pass',rows=len(frame),independent_values=11)
    except Exception:result['status']='fail';raise
    finally:
        if not first.exists():first.write_text(json.dumps(result,indent=2)+'\n')


@pytest.mark.acceptance('P04-A7')
def test_refresh_earlier_year_replaces_complete_partition(tmp_path,monkeypatch):
    monkeypatch.setenv('USDA_FAS_API_KEY','SYNTHETIC_ESR_KEY')
    store=Store(tmp_path);seed(store,['esr-401-2025','esr-401-2026'])
    download_export_sales(['401'],[2025,2026],data_dir=tmp_path)
    before=store.latest('export-sales','401-2025');newer=store.latest('export-sales','401-2026')
    old=json.loads(payload('esr-401-2025')[0]);modified=old[1:];modified[0]['currentMYNetSales']=-654321
    requests=[]
    def handler(request):
        requests.append(request.url.path)
        assert request.headers['X-Api-Key']=='SYNTHETIC_ESR_KEY'
        if request.url.path==esr.path_for(401,2025):return httpx.Response(200,json=modified)
        if request.url.path==esr.path_for(401,2026):return httpx.Response(200,content=payload('esr-401-2026')[0])
        name=request.url.path.rsplit('/',1)[-1]
        return httpx.Response(200,content=payload(name)[0])
    with HTTPClient(transport=httpx.MockTransport(handler)) as client:
        output=list(esr.iter_download(['401'],[2025,2026],data_dir=tmp_path,refresh=True,client=client))
    assert esr.path_for(401,2025) in requests and esr.path_for(401,2026) in requests
    latest=store.latest('export-sales','401-2025')
    assert latest['rows']==before['rows']-1 and latest['snapshot_id']!=before['snapshot_id']
    assert store.latest('export-sales','401-2026')['snapshot_id']==newer['snapshot_id']
    assert (store.root/before['csv_path']).exists()
    assert (output[0]['currentMYNetSales']==Decimal(-654321)).any()
    removed=old[0]
    assert not ((output[0]['countryCode']==str(removed['countryCode']))&(output[0]['source_week_raw']==removed['weekEndingDate'])).any()


@pytest.mark.acceptance('P04-A5')
def test_missing_credentials_never_produce_empty_success(tmp_path,monkeypatch):
    monkeypatch.delenv('USDA_FAS_API_KEY',raising=False);monkeypatch.chdir(tmp_path)
    with pytest.raises(AuthenticationError):download_export_sales(['401'],[2026],data_dir=tmp_path/'data')
    assert not list((tmp_path/'data').rglob('*.latest.json'))


@pytest.mark.live
@pytest.mark.acceptance('P04-A1')
def test_authenticated_dictionaries_numeric_and_completeness():
    store=Store(OUT/'live/data')
    with HTTPClient(fas.client_config()) as client:
        dictionaries,artifacts=esr.discover(client,store,refresh=True)
        body,receipt=fas.cached_response(store,esr.path_for(401,2026),client=client,refresh=True)
        frame=esr.parse(body,dictionaries,receipt,commodity=401,market_year=2026)
        single,single_receipt=fas.cached_response(store,esr.path_for(401,2026,'1220'),client=client,refresh=True)
        country_rows=json.loads(single);subset=[r for r in json.loads(body) if r['countryCode']==1220]
        assert sorted(subset,key=lambda r:r['weekEndingDate'])==sorted(country_rows,key=lambda r:r['weekEndingDate'])
        assert len(frame)>0 and len(country_rows)>0
        atomic_write(OUT/'live/authenticated_checks.json',canonical({'dictionary_counts':{k:len(v) for k,v in dictionaries.items()},'dictionary_artifacts':artifacts,'observation_receipt':receipt,'country_receipt':single_receipt,'source_fields':sorted(json.loads(body)[0]),'rows':len(frame),'country_rows':len(country_rows),'completeness_check':'complete-array schema and independent destination endpoint equality','status':'pass'}))
