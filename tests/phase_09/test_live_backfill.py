"""Bounded real-source checks in an isolated root; production exports are untouched."""
import io,json
from pathlib import Path
import pdfplumber
import pytest
from usda_data.sources import reports
from usda_data.storage import Store,canonical,atomic_write
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/acceptance/phase-09'

@pytest.mark.live
@pytest.mark.acceptance('P09-A1')
def test_live_frozen_directory_candidate_inventory(tmp_path):
    store=Store(tmp_path/'data')
    with HTTPClient(HTTPConfig(trust_environment=False,max_attempts=2)) as client:
        body,receipt=reports.fetch_public(client,store,reports.DIRECTORY,'json',refresh=True)
    directory=json.loads(body)
    periods=sorted({f'{int(y["CalendarYear"]):04}-{int(m["Item1"]):02}' for y in directory['CircularSets'] for m in y['Months'] if '2010-01'<=f'{int(y["CalendarYear"]):04}-{int(m["Item1"]):02}'<='2026-11'})
    assert len(periods)*3==json.loads((OUT/'resource_estimate.json').read_text())['report_candidates']
    atomic_write(OUT/'resume/live_inventory_check.json',canonical({'periods':periods,'receipt':receipt,'status':'pass','scope':'Archive candidate inventory at the frozen cutoff; not proof that every attachment parses'}))

@pytest.mark.live
@pytest.mark.acceptance('P09-A4')
def test_live_corrected_official_attachments(tmp_path):
    records=json.loads((OUT/'resume/resolved_attachments.json').read_text());store=Store(tmp_path/'data');checks=[]
    with HTTPClient(HTTPConfig(trust_environment=False,max_attempts=2)) as client:
        for record in [r for r in records if r['report_period'] in {'2015-05','2014-09','2015-04'}]:
            body,receipt=reports.fetch_public(client,store,record['url'],'pdf',refresh=True)
            with pdfplumber.open(io.BytesIO(body)) as pdf:period=reports.report_period(pdf)
            assert period==record['report_period']
            assert receipt['source_artifact_id']==record['source_artifact_id']
            checks.append({'family':record['report_family'],'period':period,'receipt':receipt,'status':'pass'})
    assert len(checks)==3
    atomic_write(OUT/'resume/live_alternate_checks.json',canonical(checks))
