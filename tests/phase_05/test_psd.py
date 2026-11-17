from decimal import Decimal
from pathlib import Path
import csv
import json
import httpx
import pandas as pd
import pytest
from usda_data.sources import fas_psd as psd
from usda_data.sources import fas_common as fas
from usda_data.storage import Store,atomic_write,canonical,sha256
from usda_data.http import HTTPClient
from usda_data.api import download_psd
from usda_data.cli import main
from usda_data.errors import FormatError,ValidationError,ConfigurationError

ROOT=Path(__file__).resolve().parents[2];FIX=ROOT/'tests/fixtures/phase_05';OUT=ROOT/'artifacts/acceptance/phase-05'
CAT=json.loads((FIX/'catalog.json').read_text());REFS=json.loads((FIX/'references.json').read_text());DICT={n:json.loads((FIX/(n+'.json')).read_text()) for n in psd.DICTIONARIES}


def payload(id):
    p=FIX/(id+'.json');a=json.loads(Path(str(p)+'.acquisition.json').read_text());body=p.read_bytes()
    assert sha256(body)==a['sha256'] and a['status']==200
    return body,{'source_artifact_id':a['sha256'],'retrieved_at_utc':a['checked_at_utc']}


def load(id):
    body,receipt=payload(id);_,code,year=id.split('-');acc={}
    expected=next(e['expected_records'] for e in CAT if e['id']==id)
    frame=psd.parse(body,DICT,receipt,commodity=code,market_year=year,geography='world' if id.startswith('world') else 'all',expected_records=expected,accounting=acc)
    assert len(frame)+sum(acc['excluded_attributes'].values())==expected
    return frame


def fixtures_for_corn():
    endpoints={n:'/api/psd/'+n for n in psd.DICTIONARIES}
    endpoints.update({'release-0440000':'/api/psd/commodity/0440000/dataReleaseDates','psd-0440000-2025':psd.path_for('0440000',2025),'world-0440000-2025':psd.path_for('0440000',2025,'world')})
    return endpoints


def seed(store):
    for id,path in fixtures_for_corn().items():
        body,_=payload(id);url=fas.BASE+path;r=store.raw(body,metadata={'url':url})
        atomic_write(store.root/'manifests/fas/urls'/f'{sha256(url.encode())}.json',canonical(r))


@pytest.mark.acceptance('P05-A2')
def test_independent_values_and_dimensions():
    checks=[];frames={}
    for ref in REFS:
        if ref['role']=='holdout':continue
        id=Path(ref['artifact']).stem
        if id not in frames:frames[id]=load(id)
        dims=ref['dimensions'];frame=frames[id]
        row=frame[(frame['countryCode']==dims['countryCode'])&(frame['attributeId']==str(dims['attributeId']))]
        assert len(row)==1;row=row.iloc[0]
        for k,v in dims.items():assert row[k]==str(v)
        assert row['value']==Decimal(ref['expected_value']) and row['unit']==ref['expected_unit']
        checks.append({'reference_id':ref['id'],'source_url':ref['source_url'],'sha256':ref['sha256'],'locator':json.dumps(ref['locator']),'expected_value':ref['expected_value'],'actual_value':str(row['value']),'unit':row['unit'],'status':'pass','tolerance':'0'})
    assert len(checks)>=40
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


@pytest.mark.acceptance('P05-A3')
def test_family_union_once_and_explicit_geographic_levels(tmp_path,monkeypatch):
    monkeypatch.setenv('USDA_FAS_API_KEY','SYNTHETIC_PSD_KEY');calls=[];lookup={path:id for id,path in fixtures_for_corn().items()}
    def handler(request):
        calls.append(request.url.path);assert request.headers['X-Api-Key']=='SYNTHETIC_PSD_KEY'
        return httpx.Response(200,content=payload(lookup[request.url.path])[0])
    with HTTPClient(transport=httpx.MockTransport(handler)) as client:
        frames=list(psd.iter_download(['Corn'],[2025],families=['world-production','grain-trade'],data_dir=tmp_path,refresh=True,client=client))
    assert calls.count(psd.path_for('0440000',2025))==1
    assert calls.count(psd.path_for('0440000',2025,'world'))==1
    frame=frames[0]
    assert set(frame['aggregation_level'])=={'country','region','world'}
    assert set(frame[frame['countryCode']=='00']['aggregation_level'])=={'world'}
    assert set(frame[frame['countryCode']=='E4']['aggregation_level'])=={'region'}
    assert set(frame[frame['countryCode']=='US']['aggregation_level'])=={'country'}
    assert len(psd.SCOPE['commodity_union'])==37
    assert all(r['commodityName']!='Coffee, Green' for f in psd.SCOPE['families'].values() for r in f['commodities'])
    assert json.loads((ROOT/'config/psd_scope.json').read_text())==psd.SCOPE


@pytest.mark.acceptance('P05-A4')
def test_codes_units_scales_and_csv_exact(tmp_path):
    frame=load('psd-0440000-2025')
    assert set(frame['commodityCode'])=={'0440000'}
    raw=json.loads(payload('psd-0440000-2025')[0],parse_float=Decimal)
    lookup={(r['countryCode'],str(r['attributeId']),str(r['unitId'])):r['value'] for r in raw}
    for row in frame.itertuples():
        assert row.value==lookup[(row.countryCode,row.attributeId,row.unitId)]
    assert frame['unitId'].nunique()>=3
    psd.SCHEMA.write_csv(frame,tmp_path/'codes.csv')
    pd.testing.assert_frame_equal(frame,psd.SCHEMA.read_csv(tmp_path/'codes.csv'))


@pytest.mark.acceptance('P05-A5')
def test_source_local_year_balances():
    rules=json.loads((FIX/'balance_rules.json').read_text());checks=[]
    for year in rules['years']:
        frame=load(f'psd-0440000-{year}');country=frame[frame['countryCode']=='US'].set_index('attributeId')
        for formula in rules['formulas']:
            ids=[str(x) for x in formula['left']+formula['right']]
            assert set(country.loc[ids,'unitId'])=={rules['unitId']}
            left=sum((country.loc[str(i),'value'] for i in formula['left']),Decimal(0))
            right=sum((country.loc[str(i),'value'] for i in formula['right']),Decimal(0))
            assert abs(left-right)<=Decimal(rules['tolerance'])
            checks.append({'year':year,'country':'US','formula':formula,'left':str(left),'right':str(right),'tolerance':rules['tolerance'],'status':'pass'})
    (OUT/'balance_checks.json').write_text(json.dumps(checks,indent=2)+'\n')


@pytest.mark.acceptance('P05-A6')
def test_holdout_and_missing_attribute_first_run():
    first=OUT/'holdout_first_run.json';result={'status':'running','artifact':'psd-2631000-2025','selected_before_adapter':True}
    try:
        frame=load('psd-2631000-2025')
        for ref in [r for r in REFS if r['role']=='holdout']:
            d=ref['dimensions'];row=frame[(frame['countryCode']==d['countryCode'])&(frame['attributeId']==str(d['attributeId']))]
            assert len(row)==1 and row.iloc[0]['value']==Decimal(ref['expected_value']) and row.iloc[0]['unit']==ref['expected_unit']
        body,receipt=payload('psd-0440000-2025');rows=json.loads(body);without=[r for r in rows if not(r['countryCode']=='US' and r['attributeId']==28)]
        parsed=psd.parse(json.dumps(without).encode(),DICT,receipt,commodity='0440000',market_year=2025)
        assert not ((parsed['countryCode']=='US')&(parsed['attributeId']=='28')).any()
        assert len(parsed)==len(rows)-1
        result.update(status='pass',rows=len(frame),independent_values=6,missing_attribute_not_fabricated=True)
    except Exception:result['status']='fail';raise
    finally:
        if not first.exists():first.write_text(json.dumps(result,indent=2)+'\n')


@pytest.mark.acceptance('P05-A7')
def test_provenance_not_false_historical_vintages():
    frame=load('psd-0440000-2025')
    assert set(frame['vintage_type'])=={'current_revised'}
    assert frame['source_release_date'].isna().all() and frame['source_release_at_utc'].isna().all()
    assert set(frame['release_time_precision'])=={'month'}
    assert all(row.source_release_period==row.calendarYear+'-'+row.month for row in frame.itertuples())
    assert set(frame['calendarYear'])!={frame.iloc[0]['retrieved_at_utc'].strftime('%Y-%m-%d')}
    # The official country dictionary refers to R15 absent from the region dictionary.
    # Preserve the source code and label the missing metadata rather than invent a region name.
    body,receipt=payload('psd-0440000-2025');row=json.loads(body)[0];row['countryCode']='ZZ'
    sample=psd.parse(json.dumps([row]).encode(),DICT,receipt,commodity='0440000',market_year=2025)
    assert sample.iloc[0]['region_code']=='R15' and sample.iloc[0]['region_name'] is None
    assert sample.iloc[0]['region_mapping_status']=='absent_in_source_dictionary'


@pytest.mark.acceptance('P05-A8')
def test_public_cli_roundtrip_and_revision_retention(tmp_path):
    store=Store(tmp_path/'data');seed(store)
    frame=download_psd(['Corn'],[2025],data_dir=store.root)
    assert main(['fetch','--dataset','psd','--commodities','Corn','--market-years','2025','--data-dir',str(store.root),'--output-dir',str(tmp_path/'exports')])==0
    manifest=json.loads((tmp_path/'exports/psd.latest.json').read_text())
    pd.testing.assert_frame_equal(frame,psd.SCHEMA.read_csv(tmp_path/'exports'/manifest['csv_path']))
    previous=store.latest('psd','0440000-2025')
    body,_=payload('psd-0440000-2025');rows=json.loads(body);rows.pop(0);rows[0]['value']=98765
    receipt=store.raw(json.dumps(rows).encode(),metadata={'url':fas.BASE+psd.path_for('0440000',2025)})
    cache=store.root/'manifests/fas/urls'/f"{sha256((fas.BASE+psd.path_for('0440000',2025)).encode())}.json"
    atomic_write(cache,canonical(receipt))
    updated=download_psd(['Corn'],[2025],data_dir=store.root)
    latest=store.latest('psd','0440000-2025')
    assert len(updated)==len(frame)-1 and latest['snapshot_id']!=previous['snapshot_id']
    assert (updated['value']==Decimal(98765)).any() and (store.root/previous['csv_path']).exists()


@pytest.mark.acceptance('P05-A6')
def test_unknown_attributes_and_out_of_scope_rejected():
    body,receipt=payload('psd-0440000-2025');rows=json.loads(body);rows[0]['attributeId']=999999
    with pytest.raises(ValidationError):psd.parse(json.dumps(rows).encode(),DICT,receipt,commodity='0440000',market_year=2025)
    with pytest.raises(ConfigurationError):psd.parse(body,DICT,receipt,commodity='0711100',market_year=2025)


@pytest.mark.live
@pytest.mark.acceptance('P05-A1')
def test_live_authenticated_psd_and_independent_country():
    store=Store(OUT/'live/data')
    with HTTPClient(fas.client_config()) as client:
        d,artifacts=psd.discover(client,store,refresh=True)
        body,receipt=fas.cached_response(store,psd.path_for('0440000',2025),client=client,refresh=True)
        frame=psd.parse(body,d,receipt,commodity='0440000',market_year=2025)
        single,sr=fas.cached_response(store,psd.path_for('0440000',2025,'US'),client=client,refresh=True)
        subset=[r for r in json.loads(body) if r['countryCode']=='US']
        assert sorted(subset,key=lambda r:r['attributeId'])==sorted(json.loads(single),key=lambda r:r['attributeId'])
        world,wr=fas.cached_response(store,psd.path_for('0440000',2025,'world'),client=client,refresh=True)
        world_frame=psd.parse(world,d,wr,commodity='0440000',market_year=2025,geography='world')
        assert len(frame)>0 and set(world_frame['countryCode'])=={'00'}
        atomic_write(OUT/'live/checks.json',canonical({'dictionary_counts':{k:len(v) for k,v in d.items()},'dictionary_artifacts':artifacts,'observation_receipt':receipt,'country_receipt':sr,'world_receipt':wr,'rows':len(frame),'country_rows':len(subset),'world_rows':len(world_frame),'status':'pass'}))
