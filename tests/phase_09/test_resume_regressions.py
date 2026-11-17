"""Source-pinned regressions; these samples do not assert full-backfill acceptance."""
from decimal import Decimal
from pathlib import Path
import io,json
import pdfplumber
import pytest
from usda_data.sources import report_tables as tables
from usda_data.storage import hash_file
from usda_data.sync import execute,Task
from usda_data.errors import ValidationError

ROOT=Path(__file__).resolve().parents[2]
CAT=json.loads((ROOT/'tests/fixtures/phase_09/resume/catalog.json').read_text())

def source(family,period):
    item=next(r for r in CAT if r['family']==family and r['period']==period)
    path=ROOT/item['path'];assert hash_file(path)==item['sha256']
    return item,pdfplumber.open(path)


def test_reliability_inline_sections_and_unavailable_values():
    item,pdf=source('world-production','2013-06')
    with pdf:
        collector=tables.Collector(item['family'],item['period'],item['receipt'])
        text=pdf.pages[item['page']-1].extract_text(x_tolerance=1,y_tolerance=3)
        tables.parse_reliability(collector,'TABLE 18 Reliability of Production Projections',item['page'],text)
        frame,evidence=collector.finish()
    selected=frame[(frame.section_label=='COTTON')&(frame.row_label=='World')&(frame.indicator=='Root mean square error')]
    assert selected.iloc[0]['value']==Decimal('6.2')
    missing=frame[(frame.section_label=='SOYBEANS')&(frame.row_label=='World')&(frame.indicator=='Root mean square error')].iloc[0]
    assert missing['value'] is None and missing['raw_value']=='NA'
    corn=frame[(frame.section_label=='CORN')&(frame.row_label=='United States')&(frame.indicator=='Average difference')].iloc[0]
    assert corn['value']==875 and corn['unit']=='Million bushels'
    assert evidence['input_cells']==19*7


def test_summary_eighteen_geographies_without_europe_column():
    item,pdf=source('world-production','2016-05')
    with pdf:
        p=pdf.pages[item['page']-1];text=p.extract_text(x_tolerance=1,y_tolerance=3)
        collector=tables.Collector(item['family'],item['period'],item['receipt'])
        tables.parse_wap_summary(collector,text.splitlines()[0],item['page'],text,p)
        frame,_=collector.finish()
    assert frame.row_label.nunique()==18
    wheat=frame[(frame.section_label=='Wheat')&(frame.comparison_label=='May')]
    assert wheat[wheat.row_label=='World'].iloc[0]['value']==727
    assert wheat[wheat.row_label=='China'].iloc[0]['value']==130


def test_first_projection_has_no_invented_previous_month():
    item,pdf=source('world-production','2020-05')
    with pdf:
        p=pdf.pages[item['page']-1];text=p.extract_text(x_tolerance=1,y_tolerance=3)
        collector=tables.Collector(item['family'],item['period'],item['receipt'])
        tables.parse_wap_standard(collector,text.splitlines()[0],item['page'],text,2,p)
        frame,_=collector.finish()
    row=frame[(frame.row_label=='World')&(frame.indicator=='Production')&(frame.period_label=='2020/21')].iloc[0]
    assert row['value']==Decimal('768.49') and row['comparison_label']=='May'
    assert not frame.indicator.str.contains('last month').any()


@pytest.mark.parametrize('family,period,section',[('grain-trade','2023-09','COARSE GRAINS'),('oilseed-trade','2022-09','')])
def test_merged_change_labels_and_singular_attributes(family,period,section):
    item,pdf=source(family,period)
    with pdf:
        p=pdf.pages[item['page']-1];text=p.extract_text(x_tolerance=1,y_tolerance=3)
        collector=tables.Collector(family,period,item['receipt']);descriptors,words=tables.change_descriptors(p,text,section)
        for i,d in enumerate(descriptors):
            stop=descriptors[i+1]['title_top'] if i+1<len(descriptors) else p.height-60
            tables.parse_change_segment(collector,item['page'],text,words,d['descriptor'],d['data_top'],stop,True,page_object=p)
        frame,_=collector.finish()
    if family=='grain-trade':
        selected=frame[(frame.row_label=='Argentina')&(frame.comparison_label=='Previous')]
        assert dict(zip(selected.column_commodity,selected.value))=={'Corn':Decimal(24500),'Sorghum':Decimal(1100)}
    else:
        row=frame[(frame.row_label=='Argentina')&(frame.comparison_label=='Current')].iloc[0]
        assert row['indicator']=='Export' and row['value']==4700


def test_explicit_nonpublication_notice_preserves_period_and_hash():
    item,pdf=source('world-production','2013-10')
    with pdf:assert tables.report_period(pdf)=='2013-10'
    frame,evidence=tables.parse_report((ROOT/item['path']).read_bytes(),item['family'],item['receipt'],expected_period=item['period'])
    assert frame.empty and evidence['source_unavailable']['source_artifact_id']==item['sha256']
    assert evidence['source_unavailable']['report_period']=='2013-10'


def test_concurrent_resume_rejected_before_runner_or_state_mutation(tmp_path):
    import fcntl
    runs=tmp_path/'manifests/runs';runs.mkdir(parents=True)
    with (runs/'.writer.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValidationError,match='Another fetch/sync'):
            execute([Task('p','wasde',{})],data_dir=tmp_path,runner=lambda *a,**kw:pytest.fail('Runner must not execute'))
        assert not (runs/'active.json').exists()


def test_month_year_footer_never_becomes_a_blank_summary_row():
    item,pdf=source('world-production','2011-05')
    with pdf:
        page=pdf.pages[item['page']-1];text=page.extract_text(x_tolerance=1,y_tolerance=3)
        collector=tables.Collector(item['family'],item['period'],item['receipt'])
        tables.parse_wap_summary(collector,text.splitlines()[0],item['page'],text,page)
        frame,_=collector.finish()
    row=frame[(frame.section_label=='Cotton') & (frame.row_label=='World') & (frame.comparison_label=='May')]
    assert len(row)==1 and row.iloc[0]['value']==Decimal('124.7')
    assert len(frame)==6*3*19
