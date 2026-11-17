#!/usr/bin/env python3
"""Create the bounded Phase 00 inventory from saved official discovery evidence.

This reads pinned pages only. It does not fetch data or map business tables.
"""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / 'artifacts/acceptance/phase-00/discovery'

def load(name):
    return json.loads((DISC / name).read_text())

def text(s):
    return ' '.join(html.unescape(re.sub('<[^>]*>', ' ', s)).split())

def links(name):
    s = (DISC / name).read_text()
    return [html.unescape(x) for x in re.findall(r'href="([^"]+)"', s)]

def main():
    artifacts = []
    for p in sorted((ROOT / 'tests/fixtures/raw').glob('*.acquisition.json')):
        a = json.loads(p.read_text())
        if a['status'] != 200:
            continue
        name = Path(a['path']).stem
        family = ('wasde' if name.startswith('wasde') else 'ers-costs-returns' if name.startswith('ers') else 'rma-sob' if name.startswith('rma') else name.rsplit('-', 1)[0])
        role = name.rsplit('-', 1)[1]
        a.update(artifact_id=name, source=family, role=role,
                 acquisition_record=str(p.relative_to(ROOT)),
                 selected_before_adapter_implementation=True,
                 first_adapter_run='not_run; reserved for the dependent source phase')
        if name.startswith('wasde'):
            a.update(vintage='2026-10-09' if role == 'holdout' else '2026-11-10', vintage_precision='day', vintage_type='report_vintage')
            a['discovery_evidence'] = 'wasde-history-cdn.html' if role == 'supplemental' else 'wasde.html'
        elif name.startswith('ers'):
            a.update(vintage='2026-10-01', vintage_precision='day', vintage_type='current_revised_file', discovery_evidence='ers.html')
        elif name.startswith('rma'):
            a.update(vintage='2026-05-28' if role == 'layout' else None, vintage_precision='day' if role == 'layout' else 'unknown', vintage_type='layout_revision' if role == 'layout' else 'current_revised_file', discovery_evidence='rma.html')
        else:
            # The report itself supplies its month. Exact availability time is not inferred.
            a.update(vintage='2026-10' if role == 'holdout' else '2026-11', vintage_precision='month', vintage_type='report_vintage', discovery_evidence='fas-circular-inventory.json + psd-app.js + psd-circular-template.html')
        artifacts.append(a)
    catalog = {'schema_version':1, 'selection_policy':'Development and holdout bytes selected and frozen during Phase 00, before source adapter implementation. Reference transcription is allowed; do not tune future parsers against holdouts. Log their first adapter run in the source phase.', 'artifacts':artifacts, 'references_path':'tests/fixtures/references/observations.json', 'api_fixtures':'Deferred to Phases 04 and 05 with authorized USDA_FAS_API_KEY access.'}
    existing = ROOT / 'tests/fixtures/catalog.json'
    if existing.exists():
        old = json.loads(existing.read_text())
        for key in ['references_sha256', 'expected_reference_count']:
            if key in old:
                catalog[key] = old[key]
    acquired = {a['url']:a for a in artifacts}
    files = []
    def add(source, url, evidence, **extra):
        found = acquired.get(url)
        files.append(dict(source=source,url=url,discovery_evidence=evidence,
                          status='download_verified' if found else 'discovered_not_fetched',
                          artifact_id=found['artifact_id'] if found else None,**extra))
    for name in ['wasde.html','wasde-history-cdn.html']:
        for u in dict.fromkeys(links(name)):
            if re.search(r'\.(csv|xml|xls|pdf|txt|zip)(?:\?|$)',u,re.I) and ('wasde' in u.lower()):
                add('wasde',urljoin('https://www.usda.gov',u),name,period_hint=Path(urlsplit(u).path).name)
    s=(DISC/'ers.html').read_text()
    sections=list(re.finditer(r'<h3 class="usa-accordion__heading">.*?</h3>',s,re.S))
    for idx,m in enumerate(sections):
        section=text(m.group())
        fragment=s[m.end():sections[idx+1].start() if idx+1<len(sections) else len(s)]
        blocks=fragment.split('<div class="usa-collection__body">')[1:]
        for block in blocks:
            heading=re.search(r'<h3[^>]*>(.*?)</h3>',block,re.S)
            if not heading:continue
            dates=re.findall(r'<time datetime="([^"]+)">([^<]+)</time>',block)
            for u in re.findall(r'href="([^"]+)"',block):
                if re.search(r'\.(csv|xlsx|xls|zip)(?:\?|$)',u,re.I):
                    add('ers-costs-returns',urljoin('https://www.ers.usda.gov',html.unescape(u)),'ers.html',series_family=section,label=text(heading.group(1)),published_dates={text(label):date for date,label in dates})
    for u in dict.fromkeys(links('rma.html')):
        if 'state_county_crop/' in u and ('sobcov_' in u or 'sobscc_' in u or 'SOB_State_County_' in u):
            add('rma-sob',u,'rma.html',product='State/County/Crop/Coverage Level' if ('sobcov_' in u or '1989_Forward' in u) else 'earlier unsupported State/County/Crop layout',layout_support='not implemented; Phase 07 verifies')
    circulars=load('fas-circular-inventory.json')['CircularSets']
    report_months=sorted(f"{y['CalendarYear']}-{m['Item1'].zfill(2)}" for y in circulars for m in y['Months'])
    for family,code in [('world-production','production'),('grain-trade','Grain'),('oilseed-trade','Oilseeds')]:
        for month in report_months:
            year,mon=month.split('-')
            add(family,f'https://apps.fas.usda.gov/PSDOnline/Circulars/{year}/{mon}/{code}.pdf','fas-circular-inventory.json + psd-app.js + psd-circular-template.html',report_month=month,availability_caveat='Month listed globally; per-family attachment existence must be checked in Phase 06/09. Only downloaded fixtures are verified.')
    # No fabricated per-series first date: retain page/file-level boundaries only.
    inventory={'schema_version':1,'discovery_cutoff':'2026-11-12','purpose':'Frozen expected source inventory, not a backfill completion claim. Newly discovered items must be added before dependent acceptance.',
     'files':files,
     'coverage_limits':[
       {'source':'wasde','earliest':'2010-04','precision':'month','basis':'wasde-history-cdn.html linked ZIP 2010-04-to-2015-12','limitation':'Per-table first availability remains to be discovered in Phase 02; earlier PDF archive is not a supported structured layout.'},
       {'source':'ers-costs-returns','earliest':'1975','precision':'year','basis':'ers-methodology.html Scope/Coverage','limitation':'Start/end varies by commodity, enterprise, region and methodology. Historical discontinued products remain inventoried even when outside the default year window.'},
       {'source':'rma-sob','earliest':'1989','latest_listed':'2027','precision':'commodity_year','basis':'rma.html coverage-level section','limitation':'2027 commodity year can be listed in 2026; not a future publication-date claim. Older 1948-1988 layout is inventoried separately, not silently supported.'},
       {'source':'fas-reports','earliest_listed_month':min(report_months),'latest_listed_month':max(report_months),'basis':'fas-circular-inventory.json','limitation':'A listed month does not prove every family attachment exists; do not infer permanent source absence from missing months.'},
       {'source':'fas-esr','earliest':None,'basis':'swagger.json','limitation':'Authenticated dictionary, response and per-series year discovery deferred to Phase 04.'},
       {'source':'fas-psd','earliest':None,'basis':'swagger.json','limitation':'Authenticated dictionary, response and per-series year discovery deferred to Phase 05. Current revised history is not historical monthly vintages.'}],
     'gaps':[{'source':'fas-reports','period':'2025-10','status':'not_listed_requires_investigation','evidence':'fas-circular-inventory.json','next_action':'Phase 06 inspect official archive/announcements before classifying unavailability.'},{'source':'wasde','period':'2025-10','status':'not_listed_requires_investigation','evidence':'wasde-history-cdn.html','next_action':'Phase 02/09 investigate official release archive; never manufacture a report.'}],
     'api_expansion':json.loads((ROOT/'config/scope.json').read_text())['api_inventory_expansion']}
    # Tables are an initial observed index, not a completed report-to-PSD mapping.
    inventory['wasde_observed_tables']=[dict(table=e.attrib['Name'],title=e.attrib.get('sub_report_title'),unit=e.attrib.get('sub_report_subtitle')) for e in ET.parse(ROOT/'tests/fixtures/raw/wasde-development.xml').getroot().iter('Report') if e.attrib.get('Name','').startswith('sr')]
    for path,data in [('tests/fixtures/catalog.json',catalog),('config/expected_coverage.json',inventory)]:
        (ROOT/path).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'fixtures':len(artifacts),'inventory_files':len(files),'source_counts':{s:sum(f['source']==s for f in files) for s in sorted({f['source'] for f in files})}}))

if __name__=='__main__':main()
