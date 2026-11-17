"""Reconcile missing WASDE months with official notices and source issue chronology."""
from pathlib import Path
from datetime import date
import csv,json,re
import pdfplumber
from usda_data.storage import Store,hash_file,sha256,canonical,atomic_write

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/acceptance/phase-09'

def main():
    store=Store(ROOT/'data');results=[]
    for missing,publication,phrase in [('2013-10','2013-11','not published in October 2013'),('2019-01','2019-02','report for January 2019 will not be published')]:
        path=OUT/'resume/downloads'/f'wasde-{publication}-gap.pdf';receipt=json.loads(Path(str(path)+'.acquisition.json').read_text())
        assert hash_file(path)==receipt['sha256']
        with pdfplumber.open(path) as pdf:text=' '.join((pdf.pages[0].extract_text() or '').split())
        assert phrase in text
        results.append({'period':missing,'status':'source_unavailable','evidence_type':'explicit_official_nonpublication_note','source_artifact_id':receipt['sha256'],'source_url':receipt['url'],'source_path':str(path.relative_to(ROOT)),'page':1,'locator':'Opening note before WHEAT section','verified_statement':phrase})
    issues=[]
    for month in ['2025-09','2025-11']:
        url=f'https://www.usda.gov/sites/default/files/documents/oce-wasde-report-data-{month}.csv'
        receipt=json.loads((store.root/'manifests/wasde/urls'/f'{sha256(url.encode())}.json').read_text());path=store.artifact(receipt['source_artifact_id'])
        with path.open(encoding='utf-8-sig',newline='') as stream:
            rows=csv.DictReader(stream);numbers=set();dates=set()
            for row in rows:numbers.add(int(row['WasdeNumber']));dates.add(row['ReleaseDate'])
        assert len(numbers)==len(dates)==1
        issues.append({'month':month,'issue_number':next(iter(numbers)),'release_date':next(iter(dates)),'source_artifact_id':receipt['source_artifact_id'],'source_url':url})
    assert issues[1]['issue_number']==issues[0]['issue_number']+1
    path=OUT/'resume/downloads/wasde-2025-11-gap.pdf';receipt=json.loads(Path(str(path)+'.acquisition.json').read_text());assert hash_file(path)==receipt['sha256']
    with pdfplumber.open(path) as pdf:text=' '.join((pdf.pages[0].extract_text() or '').split())
    assert 'lapse in government funding from October 1 through November 12' in text
    assert f'WASDE - {issues[1]["issue_number"]}' in text
    inventory=json.loads((store.root/'manifests/wasde/discovery.json').read_text());assert not any('2025-10' in r['url'] for r in inventory['links'])
    result={'period':'2025-10','status':'source_unavailable','evidence_type':'source_issue_chronology_and_explicit_funding_lapse_note','source_artifact_id':receipt['sha256'],'source_url':receipt['url'],'source_path':str(path.relative_to(ROOT)),'page':1,'locator':'Opening note, issue masthead, and adjacent official structured CSV issue identifiers','issue_chronology':issues,'inference':'September and November carry consecutive official WASDE issue numbers, while November explicitly records the October 1–November 12 funding lapse. Combined with the official structured inventory, this supports no intervening October WASDE issue; this conclusion is not based on HTTP 404 or an absent directory entry alone.','verified_statement':'Official adjacent issues are consecutive; October has no structured report partition at the frozen cutoff.'}
    results.append(result)
    dates={p.name.removesuffix('.latest.json')[:7] for p in (store.root/'manifests/wasde').glob('*.latest.json')}
    expected={f'{year:04}-{month:02}' for year in range(2010,2027) for month in range(1,13) if '2010-04'<=f'{year:04}-{month:02}'<='2026-11'}
    missing=expected-dates;assert missing=={r['period'] for r in results}
    atomic_write(OUT/'wasde_gap_evidence.json',canonical({'status':'pass','supported_months':len(expected),'available_months':len(expected&dates),'missing_months':sorted(missing),'gaps':results,'unsupported_before':'2010-01 through 2010-03: first official structured archive begins April 2010'}));print({'status':'pass','missing_months':sorted(missing),'issue_chronology':issues})

if __name__=='__main__':main()
