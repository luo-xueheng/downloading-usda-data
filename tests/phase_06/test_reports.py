from datetime import date
from decimal import Decimal
from pathlib import Path
import csv,io,json
import pandas as pd
import pytest
from pypdf import PdfReader,PdfWriter
from usda_data.sources import reports,report_tables,report_datasets,fas_psd,fas_common
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
from usda_data.storage import Store,atomic_write,canonical,sha256
from usda_data.api import download_dataset,download_reports
from usda_data.cli import main
from usda_data.errors import FormatError,ValidationError

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/acceptance/phase-06';FIX=ROOT/'tests/fixtures/phase_06'
CAT=json.loads((ROOT/'tests/fixtures/catalog.json').read_text())['artifacts'];REFS=json.loads((FIX/'references.json').read_text())


def artifact(family,role):
    item=next(a for a in CAT if a['artifact_id']==family+'-'+role)
    body=(ROOT/item['path']).read_bytes();assert sha256(body)==item['sha256']
    return body,{'source_artifact_id':item['sha256'],'retrieved_at_utc':item['checked_at_utc']},item


@pytest.fixture(scope='module')
def parsed_reports():
    result={}
    for family in reports.FAMILIES:
        for role in ['development','holdout']:
            body,receipt,item=artifact(family,role)
            result[(family,role)]=report_tables.parse_report(body,family,receipt,expected_period=item['vintage'])
    return result


def seed_url(store,url,body):
    receipt=store.raw(body,metadata={'url':url})
    atomic_write(store.root/'manifests/reports/urls'/f'{sha256(url.encode())}.json',canonical(receipt))
    return receipt


def seed_reports(store,family):
    directory=(ROOT/'artifacts/acceptance/phase-00/discovery/fas-circular-inventory.json').read_bytes()
    seed_url(store,reports.DIRECTORY,directory)
    _,_,slug=reports.FAMILIES[family];landing='https://www.fas.usda.gov/data/'+slug
    source=OUT/'discovery'/('production-search.html' if family=='world-production' else family+'.html')
    seed_url(store,landing,source.read_bytes())
    for role,stamp in [('development','11102026'),('holdout','10092026')]:
        body,_,item=artifact(family,role);seed_url(store,item['url'],body)
        detail=OUT/'discovery'/('production-'+stamp+'.html' if family=='world-production' else family+'-'+stamp+'.html')
        seed_url(store,landing+'-'+stamp,detail.read_bytes())


@pytest.mark.acceptance('P06-A1')
def test_two_dates_each_archived_and_verified(tmp_path):
    result=[]
    for family in reports.FAMILIES:
        store=Store(tmp_path/family);seed_reports(store,family)
        manifest=download_reports(family,'2026-10-01','2026-11-30',data_dir=store.root)
        assert len(manifest)==2
        assert set(manifest['report_period'])=={'2026-10','2026-11'}
        assert set(manifest['source_release_date'])=={'2026-10-09','2026-11-10'}
        for r in manifest.to_dict('records'):
            assert sha256((store.root/r['attachment_path']).read_bytes())==r['source_artifact_id']
        result.extend(manifest.to_dict('records'))
    (OUT/'archive_checks.json').write_text(json.dumps(result,indent=2)+'\n')


@pytest.mark.acceptance('P06-A2')
def test_72_independent_report_cells(parsed_reports):
    checks=[]
    for ref in REFS:
        frame,_=parsed_reports[(ref['family'],ref['role'])];selected=frame
        for key in ['table_title','section_label','row_label','indicator','period_label','comparison_label','unit']:
            selected=selected[selected[key]==ref[key]]
        assert len(selected)==1,ref['reference_id']
        row=selected.iloc[0]
        assert row['value']==Decimal(ref['value']) and row['source_page']==ref['page']
        assert row['source_artifact_id']==ref['sha256'] and row['report_period']==ref['report_period']
        checks.append({'reference_id':ref['reference_id'],'source_url':ref['source_url'],'sha256':ref['sha256'],'page':ref['page'],'table':ref['table_title'],'row':ref['row_label'],'indicator':ref['indicator'],'period':ref['period_label'],'comparison':ref['comparison_label'],'expected_value':ref['value'],'actual_value':str(row['value']),'unit':row['unit'],'status':'pass','tolerance':'0'})
    assert len(checks)==72
    with (OUT/'source_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


@pytest.mark.acceptance('P06-A3')
def test_complete_required_table_coverage_and_accounting(parsed_reports):
    inventory=json.loads((ROOT/'config/report_table_inventory.json').read_text())
    rows=[];summaries=[]
    for (family,role),(frame,evidence) in parsed_reports.items():
        required={report_tables.identity(t['table_title']) for t in inventory['tables'] if t['family']==family and t['required']}
        observed={report_tables.identity(t['table_title']) for t in evidence['tables']}
        assert required==observed
        assert sum(frame['source_occurrences'])==evidence['input_cells']
        assert evidence['unique_cells']==len(frame) and all(t['input_cells']>0 for t in evidence['tables'])
        for t in evidence['tables']:
            rows.append({k:t[k] for k in ['report_family','report_period','table_title','source_page','status','layout','input_cells']})
        summaries.append({'family':family,'role':role,'input_cells':evidence['input_cells'],'unique_cells':len(frame),'duplicate_cells':evidence['duplicate_cells'],'table_instances':len(evidence['tables'])})
        (OUT/f'{family}-{role}-accounting.json').write_text(json.dumps(evidence,indent=2)+'\n')
        assert set(frame['value_status'])<={'reported','not_reported','not_applicable'}
    with (ROOT/'config/report_coverage.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'coverage_summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    # Table-specific report classifications cannot be replaced by generic current PSD.
    wap=parsed_reports[('world-production','development')][0]
    assert wap['indicator'].str.contains('Root mean square').any()
    assert wap['row_label'].str.contains('Russia Winter').any()
    oil=parsed_reports[('oilseed-trade','development')][0]
    assert (oil['source_occurrences']>1).any() # explicit identical Canada/Brazil report duplicates
    assert (oil['value_status']=='not_reported').any()


@pytest.mark.acceptance('P06-A4')
def test_vintage_dimensions_and_units_gate_numeric_comparison():
    report={'report_period':'2026-10','commodity_code':'0410000','geography_code':'00','attribute_code':'28','period_label':'2026','unit':'Thousand Metric Tons','value':Decimal('822390')}
    api={**report,'value':Decimal('827505')}
    assert report_datasets.compare_aligned(report,api,api_report_period='2026-11')['status']=='vintage_difference'
    with pytest.raises(ValidationError):report_datasets.compare_aligned(report,api,api_report_period='2026-10')
    for key,value in [('geography_code','US'),('commodity_code','0440000'),('period_label','2025'),('unit','Metric Tons')]:
        altered={**report,key:value}
        with pytest.raises(ValidationError):report_datasets.compare_aligned(report,altered,api_report_period='2026-10')
    assert report_datasets.compare_aligned(report,report,api_report_period='2026-10')['status']=='pass'
    (OUT/'vintage_comparison.json').write_text(json.dumps({'report_artifact':'world-production-holdout','report_period':'2026-10','report_world_wheat_production_million_tons':'822.39','later_report_period':'2026-11','later_report_world_wheat_production_million_tons':'827.51','status':'demonstrated_report_vintage_difference','api_comparison_policy':'Do not claim a same-publication API match from a month-only source update timestamp.'},indent=2)+'\n')


def seed_psd_sample(store,family):
    code='2222000' if family=='oilseed-trade' else '0440000'
    root=ROOT/'tests/fixtures/phase_05'
    endpoints={name:'/api/psd/'+name for name in fas_psd.DICTIONARIES}
    endpoints.update({f'release-{code}':f'/api/psd/commodity/{code}/dataReleaseDates',f'psd-{code}-2025':fas_psd.path_for(code,2025),f'world-{code}-2025':fas_psd.path_for(code,2025,'world')})
    for id,path in endpoints.items():
        body=(root/(id+'.json')).read_bytes();url=fas_common.BASE+path;receipt=store.raw(body,metadata={'url':url})
        atomic_write(store.root/'manifests/fas/urls'/f'{sha256(url.encode())}.json',canonical(receipt))
    return code


@pytest.mark.acceptance('P06-A5')
def test_all_three_public_interfaces_and_csv(tmp_path):
    outputs=[]
    for family in reports.FAMILIES:
        store=Store(tmp_path/family);seed_reports(store,family);code=seed_psd_sample(store,family)
        frame=download_dataset(family,data_dir=store.root,market_years=[2025],report_start='2026-11-01',report_end='2026-11-30',commodities=[code])
        assert set(frame['observation_kind'])=={'psd_current','report_table'}
        assert not frame.duplicated(report_datasets.SCHEMA.keys).any()
        assert set(frame[frame['observation_kind']=='psd_current']['commodity_code'])=={code}
        assert set(frame[frame['observation_kind']=='report_table']['vintage_type'])=={'report_vintage'}
        assert set(frame[frame['observation_kind']=='psd_current']['vintage_type'])=={'current_revised'}
        export=tmp_path/(family+'-exports')
        assert main(['fetch','--dataset',family,'--market-years','2025','--commodities',code,'--report-start','2026-11-01','--report-end','2026-11-30','--with-reports','--data-dir',str(store.root),'--output-dir',str(export)])==0
        manifest=json.loads((export/(family+'.latest.json')).read_text())
        pd.testing.assert_frame_equal(frame,report_datasets.SCHEMA.read_csv(export/manifest['csv_path']))
        outputs.append({'family':family,'rows':len(frame),'current_psd_rows':int((frame['observation_kind']=='psd_current').sum()),'report_cells':int((frame['observation_kind']=='report_table').sum()),'status':'pass'})
    (OUT/'interface_checks.json').write_text(json.dumps(outputs,indent=2)+'\n')


@pytest.mark.acceptance('P06-A6')
def test_missing_table_and_changed_layout_fail():
    body,receipt,_=artifact('world-production','development')
    reader=PdfReader(io.BytesIO(body));writer=PdfWriter()
    for i,page in enumerate(reader.pages):
        if i!=19:writer.add_page(page)
    stream=io.BytesIO();writer.write(stream)
    with pytest.raises((FormatError,ValidationError)):report_tables.parse_report(stream.getvalue(),'world-production',receipt,expected_period='2026-11')
    changed='World Wheat Production, Consumption, and Stocks\nThousand Metric Tons\n2022/23 2023/24 2024/25 2025/26 2026/27 2026/27\nProduction\nChina 1 2 3 4 5\n'
    collector=report_tables.Collector('grain-trade','2026-11',receipt)
    with pytest.raises((FormatError,ValidationError)):
        report_tables.parse_year_columns(collector,'World Wheat Production, Consumption, and Stocks',1,changed);collector.finish()


@pytest.mark.live
@pytest.mark.acceptance('P06-A1')
def test_live_six_original_report_attachments(tmp_path):
    checks=[];store=Store(OUT/'live/data')
    with HTTPClient(HTTPConfig(trust_environment=False)) as client:
        for family in reports.FAMILIES:
            records=list(reports.iter_reports(family,'2026-10-01','2026-11-30',data_dir=store.root,refresh=True,client=client))
            assert len(records)==2 and {r['report_period'] for r in records}=={'2026-10','2026-11'}
            for r in records:
                body=store.artifact(r['source_artifact_id']).read_bytes()
                assert body.startswith(b'%PDF-') and sha256(body)==r['source_artifact_id']
                checks.append(r)
    atomic_write(OUT/'live/report_checks.json',canonical(checks))
