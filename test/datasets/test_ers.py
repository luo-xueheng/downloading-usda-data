from pathlib import Path
from decimal import Decimal
import csv
import io
import json
import zipfile
import xlrd
import openpyxl
import pandas as pd
import pytest
from usda_data.sources import ers_costs_returns as ers
from usda_data.storage import Store,atomic_write,canonical,sha256
from usda_data.http import HTTPClient
from usda_data.errors import FormatError,ValidationError,ConfigurationError
from usda_data.api import download_costs_returns,download_dataset
from usda_data.cli import main,export_frames

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.cache/test-output/phase-03'
FIX=ROOT/'test/fixtures/phase_03'
META=json.loads((FIX/'discovery_manifest.json').read_text())
REFS=json.loads((FIX/'references.json').read_text())
HOLDOUT_ID='4928'


def getmeta(id):
    return next(r for r in META if r['product_id']==id)


def fixture(meta):
    path=FIX/(meta['product_id']+'-'+meta['url'].split('?')[0].rsplit('/',1)[1])
    acquisition=json.loads(Path(str(path)+'.acquisition.json').read_text())
    assert acquisition['status']==200, f"Required official fixture missing: {path.name}"
    assert sha256(path.read_bytes())==acquisition['sha256']
    receipt={'source_artifact_id':acquisition['sha256'],'retrieved_at_utc':acquisition['checked_at_utc']}
    return path,receipt


def load(id,**kwargs):
    meta=getmeta(id);path,receipt=fixture(meta);acc={}
    frame=ers.parse(path,meta,receipt,accounting=acc,**kwargs)
    return frame,acc


def seed(store,ids):
    selected=[]
    for id in ids:
        meta=getmeta(id);path,_=fixture(meta)
        receipt=store.raw(path.read_bytes(),metadata={'url':meta['url']})
        atomic_write(store.root/'manifests/costs-returns/urls'/f'{sha256(meta["url"].encode())}.json',canonical(receipt))
        selected.append(meta)
    atomic_write(store.root/'manifests/costs-returns/discovery.json',canonical(selected))


@pytest.mark.acceptance('P03-A2')
def test_independent_references():
    checks=[];frames={}
    for ref in REFS:
        if ref['role']=='holdout':continue
        id=Path(ref['artifact']).name.split('-')[0]
        if id not in frames:frames[id]=load(id)[0]
        frame=frames[id];locator=json.dumps(ref['locator'],sort_keys=True)
        actual=frame[frame['source_locator']==locator]
        assert len(actual)==1,ref['id']
        actual=actual.iloc[0]
        if ref['expected_raw']=='':assert actual['value'] is None
        else:assert actual['value']==Decimal(ref['expected_raw']),ref['id']
        assert actual['unit']==ref['expected_unit'],ref['id']
        if 'dimensions' in ref:
            for source,dest in [('Commodity','commodity'),('Category','category'),('Region','region'),('Year','year_label'),('Country','country'),('Size','size'),('Survey base year','methodology')]:
                if source in ref['dimensions']:assert actual[dest]==ref['dimensions'][source]
            assert actual['source_item']==ref['dimensions']['Item']
        if 'year_label' in ref:assert actual['year_label']==ref['year_label']
        assert sha256((ROOT/ref['artifact']).read_bytes())==ref['sha256']
        checks.append({'reference_id':ref['id'],'source_url':ref['url'],'sha256':ref['sha256'],'locator':locator,'expected_value':ref['expected_raw'],'actual_value':str(actual['value']),'unit':actual['unit'],'status':'pass','tolerance':'0'})
    assert len(checks)>=30
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


@pytest.mark.acceptance('P03-A3')
def test_all_observed_layouts_and_numeric_cell_accounting():
    results=[]
    for meta in META:
        if meta['product_id']==HOLDOUT_ID:continue
        path,receipt=fixture(meta);acc={}
        frame=ers.parse(path,meta,receipt,accounting=acc)
        assert len(frame)>0
        assert len(frame)==acc['mapped_rows']==acc['input_data_cells']
        assert acc['quarantined_rows']==0
        if meta['format']=='xls':
            book=xlrd.open_workbook(path)
            mapped={tuple(json.loads(r['source_locator'])[k] for k in ['sheet','row','column']) for r in frame.to_dict('records') if r['value'] is not None}
            numeric=set()
            for sheet in book.sheets():
                for i in range(sheet.nrows):
                    if str(sheet.cell_value(i,0)).strip().lower()=='item':continue
                    for j in range(sheet.ncols):
                        if sheet.cell_type(i,j)==xlrd.XL_CELL_NUMBER:numeric.add((sheet.name,i+1,j+1))
            assert mapped==numeric,path.name
        results.append({'file':path.name,'source_sha256':receipt['source_artifact_id'],'rows':len(frame),'accounting':acc,'status':'pass'})
    (OUT/'layout_coverage.json').write_text(json.dumps(results,indent=2)+'\n')
    assert len(results)==len(META)-1


@pytest.mark.acceptance('P03-A4')
def test_methods_forecast_vintages_and_status():
    recent,_=load('4962');historical,_=load('4927');forecast,_=load('4924')
    assert set(recent['estimate_status'])=={'unknown'}
    assert set(forecast['estimate_status'])=={'forecast'}
    assert forecast['forecast_vintage'].nunique()==14
    assert any(forecast.groupby(['commodity','year','item']).forecast_vintage.nunique()>1)
    assert historical['methodology'].str.contains('economic_full_ownership').any()
    assert historical['methodology'].str.contains('cash_costs').any()
    # The same published year can exist in multiple actual source method/series contexts.
    current,_=load('4923')
    both=ers.SCHEMA.validate(pd.concat([forecast,current],ignore_index=True))
    assert len(both)==len(forecast)+len(current)
    assert both['series_family'].nunique()==2
    tobacco,_=load('4957')
    assert tobacco['classification'].str.contains('Burley').any()
    assert tobacco['classification'].str.contains('Flue-cured').any()
    assert 'Dollars per cwt' in set(tobacco['unit'])
    assert 'Dollars per acre' in set(tobacco['unit'])
    assert (tobacco['value_status']=='included_elsewhere').sum()==18


@pytest.mark.acceptance('P03-A5')
def test_independent_additive_cost_groups():
    rules=json.loads((FIX/'balance_rules.json').read_text())
    frame,_=load('4962');frame=frame[(frame['year']==2025)&(frame['region']=='U.S. total')]
    results=[]
    for group in rules['groups']:
        selected=frame[frame['category']==group['category']].set_index('item')
        assert all(c in selected.index for c in group['components'])
        components=sum((selected.loc[c,'value'] for c in group['components']),Decimal(0))
        total=selected.loc[group['total'],'value']
        tolerance=Decimal('0.005')*(len(group['components'])+1)
        assert abs(components-total)<=tolerance
        results.append({'category':group['category'],'sum':str(components),'source_total':str(total),'tolerance':str(tolerance),'status':'pass'})
    (OUT/'balance_checks.json').write_text(json.dumps(results,indent=2)+'\n')


@pytest.mark.acceptance('P03-A6')
def test_reserved_holdouts_first_run(tmp_path):
    first=OUT/'holdout_first_run.json';result={'status':'running','artifacts':json.loads((FIX/'holdouts.json').read_text())['artifacts']}
    try:
        frame,acc=load(HOLDOUT_ID)
        for ref in [r for r in REFS if r['role']=='holdout']:
            row=frame[frame['source_locator']==json.dumps(ref['locator'],sort_keys=True)]
            assert len(row)==1 and row.iloc[0]['value']==Decimal(ref['expected_raw'])
            assert row.iloc[0]['unit']==ref['expected_unit']
        assert (frame['value']<0).any() and (frame['value']==0).any()
        assert frame['unit'].nunique()>=3
        path=ROOT/'test/fixtures/raw/ers-holdout.csv'
        a=json.loads(Path(str(path)+'.acquisition.json').read_text());meta=getmeta('4976')
        soy=ers.parse(path,meta,{'source_artifact_id':a['sha256'],'retrieved_at_utc':a['checked_at_utc']})
        assert len(soy)>0 and (soy['value']<0).any()
        # Real historical missing cells (By-products, 1980-84) retain nulls.
        milk,_=load('4944');missing=milk[(milk['source_item'].str.strip()=='By-products')&(milk['year']==1980)]
        assert len(missing)==1 and missing.iloc[0]['value'] is None
        ers.SCHEMA.write_csv(frame,tmp_path/'holdout.csv')
        pd.testing.assert_frame_equal(frame,ers.SCHEMA.read_csv(tmp_path/'holdout.csv'))
        result.update(status='pass',historical_rows=len(frame),soybean_rows=len(soy),missing_cells_checked=len(missing))
    except Exception:
        result['status']='fail';raise
    finally:
        if not first.exists():first.write_text(json.dumps(result,indent=2)+'\n')


@pytest.mark.acceptance('P03-A7')
def test_public_cli_exact_csv_and_file_replacement(tmp_path):
    store=Store(tmp_path/'data');seed(store,['4962','4927','4923','4924'])
    frame=download_costs_returns([2025],commodities='Corn',data_dir=store.root)
    assert len(frame)>0 and set(frame['year'])=={2025}
    assert main(['fetch','--dataset','costs-returns','--years','2025','--commodities','Corn','--data-dir',str(store.root),'--output-dir',str(tmp_path/'exports')])==0
    manifest=json.loads((tmp_path/'exports/costs-returns.latest.json').read_text())
    pd.testing.assert_frame_equal(frame,ers.SCHEMA.read_csv(tmp_path/'exports'/manifest['csv_path']))
    pd.testing.assert_frame_equal(frame,download_dataset('costs-returns',years=[2025],commodities='Corn',data_dir=store.root))
    meta=getmeta('4962');previous=store.latest('costs-returns',meta['partition'])
    original=ers.SCHEMA.read_csv(store.root/previous['csv_path'])
    assert original['year'].nunique()>1 # full file, not only filtered newest year
    raw_path,_=fixture(meta);rows=list(csv.reader(raw_path.open(encoding='utf-8-sig')))
    rows.pop(1);rows[1][8]='-99.99'
    text=io.StringIO();writer=csv.writer(text);writer.writerows(rows)
    receipt=store.raw(text.getvalue().encode(),metadata={'url':meta['url']})
    atomic_write(store.root/'manifests/costs-returns/urls'/f'{sha256(meta["url"].encode())}.json',canonical(receipt))
    after=download_costs_returns([2025],commodities='Corn',data_dir=store.root)
    latest=store.latest('costs-returns',meta['partition'])
    assert latest['rows']==previous['rows']-1 and latest['snapshot_id']!=previous['snapshot_id']
    assert (after['value']==Decimal('-99.99')).any()
    assert (store.root/previous['csv_path']).exists()


@pytest.mark.acceptance('P03-A3')
def test_unknown_fields_and_wide_layouts_fail(tmp_path):
    meta=getmeta('4962');p,receipt=fixture(meta)
    broken=tmp_path/'broken.csv'
    rows=list(csv.reader(p.open(encoding='utf-8-sig')));rows[0][0]='Wrong'
    with broken.open('w',newline='') as stream:
        csv.writer(stream).writerows(rows)
    with pytest.raises(FormatError):ers.parse(broken,meta,receipt)
    with pytest.raises(ConfigurationError):ers.validate_years('2025:2020')
    rows=[['Item',2020],['unlabelled number',1]]
    with pytest.raises(FormatError):list(ers.wide_rows(rows,getmeta('4927'),receipt,'unknown',accounting={'input_data_cells':0,'excluded':[]}))


@pytest.mark.live
@pytest.mark.acceptance('P03-A1')
def test_live_all_links_and_real_numeric_sample():
    store=Store(OUT/'live/data')
    with HTTPClient() as client:
        records=ers.discover(client,store)
        assert len(records)>=73
        assert all(r['reason'] and r['family'] and r['commodity_group'] for r in records)
        assert {'Recent','Historical','forecast','previously released forecasts'}=={r['family'] for r in records}
        frozen=json.loads((ROOT/'test/fixtures/config/expected_coverage.json').read_text())
        expected={r['url'].split('?')[0] for r in frozen['files'] if r['source']=='ers-costs-returns'}
        assert expected<={r['url'].split('?')[0] for r in records}
        meta=next(r for r in records if r['product_id']=='4962')
        body,headers=client.get(meta['url'],expected='csv');receipt=store.raw(body,metadata=headers)
        frame=ers.parse(store.artifact(receipt['source_artifact_id']),meta,receipt)
        assert len(frame)>0
        atomic_write(OUT/'live/discovery_and_sample.json',canonical({'inventory':records,'receipt':receipt,'sample_rows':len(frame)}))
