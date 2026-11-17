#!/usr/bin/env python3
"""Verify Phase 00 scope, frozen official evidence and independent references.

Standard library only. Offline mode cannot make network requests. Live mode uses
bounded unauthenticated GETs to public evidence URLs, never production outputs.
No USDA source adapter, normalization pipeline or general crawler is implemented.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DATASETS = {'wasde','export-sales','world-production','grain-trade','oilseed-trade','costs-returns','rma-sob'}
FAMILIES = {'world-production','grain-trade','oilseed-trade'}
PUBLIC = {'wasde','ers-costs-returns','rma-sob'} | FAMILIES
SOURCES = PUBLIC | {'fas-esr','fas-psd'}
DISC = 'test/fixtures/discovery/phase-00/discovery/'
EXPECTED = {
 'P00-A1':'Exactly seven datasets, exclusions, date/year semantics, family boundaries and complete frozen public-link inventory.',
 'P00-A2':'Every source has official discovery, dated access evidence and verified success or an explicit evidenced access blocker.',
 'P00-A3':'Every publication claim has a pinned official locator and precision, or an explicit unverified status; timing kinds remain distinct.',
 'P00-A4':'Real development and distinct holdout artifacts for every public numeric source and FAS report family match frozen SHA-256 and file format.',
 'P00-A5':'Every independently authored observation has exact dimensions, unit, vintage, locator and value; all selected source cells agree at source precision.',
 'P00-A6':'No credential value in delivered sources, fixtures or evidence; absent authenticated API access remains deferred to Phases 04/05.'}

class InvalidEvidence(Exception):
    pass

class ExternalBlocker(Exception):
    pass

def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)

def path(name):
    p = (ROOT / name).resolve()
    require(p.is_relative_to(ROOT.resolve()), 'Evidence path escapes repository')
    return p

def read(name):
    return json.loads(path(name).read_text())

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def pinned(name, expected):
    p=path(name)
    require(p.is_file(), f'Missing evidence: {name}')
    require(digest(p)==expected, f'SHA-256 mismatch: {name}')
    return p

def official(url):
    u=urlsplit(url)
    return u.scheme=='https' and (u.hostname=='usda.gov' or (u.hostname or '').endswith('.usda.gov') or u.hostname in {'usda.azureedge.us','fas-prod.azureedge.us'})

def anchors(name):
    return {html.unescape(u) for u in re.findall(r'href="([^"]+)"',path(DISC+name).read_text())}

def check_scope():
    s=read('test/fixtures/config/scope.json'); inv=read('test/fixtures/config/expected_coverage.json')
    require(len(s['datasets'])==7 and {d['id'] for d in s['datasets']}==DATASETS,'Dataset scope must contain exactly seven unique IDs')
    require(set(s['report_families'])==FAMILIES,'Report-family boundary changed')
    require(s['authorized_phases']==['00'],'Only Phase 00 is authorized')
    d=s['defaults']
    require(d['start_date']=='2010-01-01' and d['start_year']==2010 and d['report_start']=='2010-01-01','Default start changed without acceptance update')
    require(d['end']==d['report_end']=='latest available at run time','Latest available default missing')
    for k in ['first_available','source_year_labels','all_history','development_samples_only']:require(bool(d[k]),f'Missing date/coverage rule: {k}')
    for dataset in s['datasets']:require(bool(dataset['period_semantics']) and 'all ' in dataset['coverage'], 'Missing year meaning or full coverage')
    for f in s['report_families'].values():require(all(f.get(k) for k in ['title','circular_code','boundary']),'Incomplete report boundary')
    for excluded in ['NASS Crop Progress & Condition','NASS Crop Production','ERS separately linked Organic products','RMA Cause of Loss','FSA prevented planting','RMA Type/Practice/Unit products','unrelated PSD report families']:
        require(excluded in s['exclusions'],f'Missing exclusion: {excluded}')
    require(set(s['ers']['series'])=={'Recent','Historical','forecast','previously released forecasts'},'ERS scope narrowed')
    require(s['rma']['product']=='State/County/Crop/Coverage Level SOB','Incorrect RMA product')
    require(inv['api_expansion']==s['api_inventory_expansion'],'API expansion inventories disagree')
    urls={source:{f['url'] for f in inv['files'] if f['source']==source} for source in PUBLIC}
    expected_wasde={urljoin('https://www.usda.gov',u) for name in ['wasde.html','wasde-history-cdn.html'] for u in anchors(name) if 'wasde' in u.lower() and re.search(r'\.(csv|xml|xls|pdf|txt|zip)(?:\?|$)',u,re.I)}
    expected_ers={urljoin('https://www.ers.usda.gov',u) for u in anchors('ers.html') if '/media/' in u and re.search(r'\.(csv|xlsx|xls|zip)(?:\?|$)',u,re.I)}
    expected_rma={u for u in anchors('rma.html') if 'state_county_crop/' in u and any(x in u for x in ['sobcov_','sobscc_','SOB_State_County_'])}
    for source,expected in [('wasde',expected_wasde),('ers-costs-returns',expected_ers),('rma-sob',expected_rma)]:
        require(urls[source]==expected,f'Incomplete/extra frozen {source} file inventory')
    months={(y['CalendarYear'],m['Item1'].zfill(2)) for y in read(DISC+'fas-circular-inventory.json')['CircularSets'] for m in y['Months']}
    for family,code in [('world-production','production'),('grain-trade','Grain'),('oilseed-trade','Oilseeds')]:
        expected={f'https://apps.fas.usda.gov/PSDOnline/Circulars/{y}/{m}/{code}.pdf' for y,m in months}
        require(urls[family]==expected,f'Incomplete report-month inventory: {family}')
    require(all(f['status'] in {'discovered_not_fetched','download_verified'} for f in inv['files']),'Inventory contains unjustified completed/unavailable status')
    return f'7 datasets; {len(inv["files"])} discovered file/report candidates; all default boundaries preserved.'

def check_sources():
    r=read('test/fixtures/config/source_registry.json')
    require(len(r['sources'])==8 and {s['source_id'] for s in r['sources']}==SOURCES,'Missing source registry entries')
    count=0
    for p in path(DISC).glob('*.acquisition.json'):
        a=json.loads(p.read_text());pinned(a['path'],a['sha256']);count+=1
        require(a.get('checked_at_utc') and official(a['url']),f'Undated/nonofficial acquisition: {p.name}')
    for s in r['sources']:
        require(official(s['official_landing_page']) and s['discovery_method'] and s['access_check_date'],'Missing official discovery/date')
        for key in ['landing_evidence','verified_discovery']:
            e=s[key];pinned(e['path'],e['sha256'])
            a=read(e['path']+'.acquisition.json')
            require(a['url']==e['url'],'Acquisition URL mismatch')
            if key=='verified_discovery':require(a['status']==200,'Broken endpoint listed as verified')
        require(s['landing_status']==200 or bool(s['external_blocker']),'Failed landing without explicit external blocker')
        require(all(s.get(k) for k in ['authentication','format','coverage_limits']),'Incomplete source description')
    return f'8 sources with dated official evidence; {count} discovery responses hash-checked; canonical 403/host-root 404 explicitly retained.'

def check_publications():
    r=read('test/fixtures/config/source_registry.json');claims=r['publication_claims']
    required={'wasde-report','wasde-history','esr-weekly','esr-api','world-production-report','grain-trade-report','oilseed-trade-report','psd-api-convention','psd-directory-schedule','ers-estimates','ers-forecasts','ers-file-dates','rma-summary-refresh','rma-zip-refresh'}
    require(len(claims)==len(required) and {c['claim_id'] for c in claims}==required,'Missing/duplicate publication claims')
    for c in claims:
        require(c['precision'] and c['artifact_kind'] and 'timezone' in c and c['statement'],'Missing publication precision/kind/timezone')
        require(c['status'] in {'verified','unverified'},'Invalid publication claim status')
        if c['status']=='verified':
            e=c['evidence'];require(e and e['locator'] and official(e['url']),'Verified claim lacks official locator')
            pinned(e['path'],e['sha256'])
        else:require(c['note'] and c['precision']=='unknown','Unverified claim is not explicitly qualified')
    require('12:00pm ET' in path(DISC+'wasde.html').read_text(),'WASDE clock evidence missing')
    require('8:30 a.m. ET' in path(DISC+'esr-program-cdn.html').read_text(),'ESR clock evidence missing')
    require('each Monday morning' in path(DISC+'rma-summary.html').read_text(),'RMA refresh evidence missing')
    for family,page in [('world-production',17),('grain-trade',3),('oilseed-trade',8)]:
        t=path(DISC+family+'-development.txt').read_text().split(f'=== PDF PAGE {page} ===')[1].split('=== PDF PAGE ')[0]
        require('12:00' in t and '12:15' in t,'Report/API timing evidence missing')
    return f'{len(claims)} publication records; report/API/historical-file/ZIP timing separated; two actual-availability claims explicitly unverified.'

def check_artifacts():
    cat=read('test/fixtures/catalog.json');art=cat['artifacts']
    require(len({a['artifact_id'] for a in art})==len(art),'Duplicate artifact IDs')
    for source in PUBLIC:
        pair=[a for a in art if a['source']==source and a['role'] in {'development','holdout'}]
        require(len(pair)==2 and {a['role'] for a in pair}=={'development','holdout'},f'Missing initial/holdout: {source}')
        require(len({a['sha256'] for a in pair})==2,'Holdout duplicates development artifact')
    for a in art:
        p=pinned(a['path'],a['sha256']);raw=p.read_bytes()
        acq=read(a['acquisition_record'])
        require(acq['sha256']==a['sha256'] and acq['url']==a['url'] and acq['status']==200,'Raw acquisition mismatch')
        require(official(a['url']) and a['selected_before_adapter_implementation'],'Invalid fixture origin/selection')
        require(a['bytes']==len(raw)>0 and a['discovery_evidence'],'Empty fixture/missing discovery')
        if p.suffix=='.pdf':require(raw.startswith(b'%PDF-') and b'%%EOF' in raw[-2048:],'Invalid PDF bytes')
        elif p.suffix=='.xml':require(ET.fromstring(raw).tag=='Report','Wrong XML document')
        elif p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                require(z.testzip() is None and bool(z.namelist()),'ZIP CRC/empty archive failure')
                require(all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist()),'Unsafe archive member')
        elif p.suffix=='.csv':
            header=next(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
            require('Value' in header,'HTML/error or unexpected CSV fixture')
        else:raise InvalidEvidence('Unexpected fixture format')
    return f'{len(art)} real raw artifacts hash/format-verified; six development/holdout pairs plus layout and supplemental CSV.'

def reference_value(ref, artifacts):
    a=artifacts[ref['artifact_id']];spec=ref['readback'];p=path(a['path'])
    if spec['kind']=='csv':
        with p.open(encoding='utf-8-sig',newline='') as f:
            row=next(row for i,row in enumerate(csv.DictReader(f),1) if i==spec['row'])
        require(ref['dimensions']==spec['dimension_columns'],'CSV reference dimensions disagree with its locator')
        require(all(row[k]==v for k,v in spec['dimension_columns'].items()),'CSV dimensions do not match reference')
        require(row[spec['unit_column']]==ref['expected_unit'],'CSV unit mismatch')
        return row[spec['column']]
    if spec['kind']=='xml':
        root=ET.parse(p).getroot()
        nodes=[e for e in root.findall(spec['xpath']) if spec['attribute'] in e.attrib]
        require(len(nodes)==1,'XML cell locator is missing/ambiguous')
        parents={child:parent for parent in root.iter() for child in parent}
        chain=[]; current=nodes[0]
        while current in parents:
            current=parents[current];chain.append(current)
        for dimension,attribute in [('table','Name'),('geography','commodity_header1'),('commodity','commodity1'),('market_year','market_year1'),('forecast_month','forecast_month1'),('indicator','attribute1')]:
            require(any(e.attrib.get(attribute)==ref['dimensions'][dimension] for e in chain),'XML reference dimensions mismatch')
        require(root.find(spec['unit_xpath']).attrib[spec['unit_attribute']]==ref['expected_unit'],'XML unit mismatch')
        return nodes[0].attrib[spec['attribute']]
    if spec['kind']=='zip_pipe':
        with zipfile.ZipFile(p) as z, z.open(spec['member']) as f:
            line=next(line for i,line in enumerate(f,1) if i==spec['line'])
        fields=line.decode('utf-8-sig').strip('\r\n').split('|')
        require(len(fields)==spec['expected_width'],'RMA row width differs from layout')
        require(all(fields[int(k)-1].strip()==v for k,v in spec['dimension_fields'].items()),'RMA grouping dimensions mismatch')
        for column,dimension in [(1,'commodity_year'),(2,'state_code'),(3,'state_abbreviation'),(4,'county_code'),(5,'county_name'),(6,'commodity_code'),(7,'commodity_name'),(8,'insurance_plan_code'),(9,'insurance_plan_abbreviation'),(10,'coverage_category'),(11,'delivery_type'),(12,'coverage_level'),(18,'quantity_type')]:
            require(fields[column-1].strip()==ref['dimensions'][dimension],'RMA reference dimensions disagree with raw fields')
        indicator,unit={13:('Policies Sold Count','policies'),19:('Net Reported Quantity',fields[17].strip()),27:('Indemnity Amount ($)','USD')}[spec['field']]
        require(ref['dimensions']['indicator']==indicator and ref['expected_unit']==unit,'RMA field meaning/unit mismatch')
        if spec['unit_field']:require(fields[spec['unit_field']-1].strip()==ref['expected_unit'],'RMA quantity unit mismatch')
        require(spec['layout_artifact_id'] in artifacts,'Missing official layout')
        return fields[spec['field']-1].strip()
    if spec['kind']=='pdf_independent_transcript':
        t=pinned(spec['transcript_path'],spec['transcript_sha256']).read_text()
        pinned(spec['image_path'],spec['image_sha256'])
        require(spec['visual_checked'] and spec['page']>0,'PDF visual reference missing')
        if 'regex' in spec:
            for dim in ['commodity','geography','market_year']:
                require(ref['dimensions'][dim].lower() in ' '.join(t.lower().split()),'PDF narrative dimension missing')
            require(ref['expected_unit']=={'Production':'million metric tons','Yield':'tons per hectare','Harvested area':'million hectares'}[ref['dimensions']['indicator']],'PDF narrative unit mismatch')
            matches=re.findall(spec['regex'],' '.join(t.split()))
            require(len(matches)==1,'PDF paragraph locator missing/ambiguous')
            return matches[0]
        require(spec['unit_text'] in t and ref['expected_unit'] in spec['unit_text'],'PDF unit/header mismatch')
        require(ref['dimensions']['indicator']==spec['section_start'],'PDF indicator/section mismatch')
        require(ref['dimensions']['market_year'] in t,'PDF marketing-year header missing')
        require(ref['dimensions']['column_month']==('Nov' if a['role']=='development' else 'Oct'),'PDF selected-column vintage mismatch')
        if a['source']=='grain-trade':
            require(ref['dimensions']['geography']==spec['row_label'] and ref['dimensions']['commodity']=='Wheat','Grain table dimension mismatch')
        else:
            require(ref['dimensions']['commodity']==spec['row_label'] and ref['dimensions']['geography']=='World','Oilseed table dimension mismatch')
        section=t.split(spec['section_start'],1)[1].split(spec['section_end'],1)[0]
        rows=[line.strip() for line in section.splitlines() if line.strip().startswith(spec['row_label']+' ')]
        require(len(rows)==1,'PDF table row locator missing/ambiguous')
        return rows[0].split()[spec['column_token']]
    raise InvalidEvidence('Unsupported reference reader')

def check_references(comparisons=None):
    cat=read('test/fixtures/catalog.json');refs=read(cat['references_path'])['observations']
    pinned(cat['references_path'],cat['references_sha256'])
    require(len(refs)==cat['expected_reference_count']>0,'Empty/incomplete reference inventory')
    require(len({r['reference_id'] for r in refs})==len(refs),'Duplicate reference ID')
    arts={a['artifact_id']:a for a in cat['artifacts']}
    for a in arts.values():
        if a['role'] in {'development','holdout'}:require(any(r['artifact_id']==a['artifact_id'] for r in refs),'Fixture lacks independent observations')
    errors=[]
    for ref in refs:
        result='pass';observed='';error=''
        try:
            a=arts[ref['artifact_id']]
            for k in ['locator','dimensions','expected_value','expected_unit','vintage_precision','reference_creation_method']:require(bool(ref.get(k)),f'Missing reference {k}')
            require('vintage' in ref and (ref['vintage'] is not None or ref['vintage_precision']=='unknown'),'Unspecified vintage')
            require(ref['artifact_sha256']==a['sha256'] and ref['source_url']==a['url'],'Reference artifact provenance mismatch')
            require(all(ref[k]==a[k] for k in ['source','vintage','vintage_precision','vintage_type']),'Reference vintage/source mismatch')
            require(ref['fixture_role']==a['role'],'Reference fixture-role mismatch')
            require(ref['tolerance']=='0','Reference tolerance changed')
            observed=reference_value(ref,arts)
            ov=Decimal(observed.replace(',',''));ev=Decimal(ref['expected_value'])
            require(ov.is_finite() and ev.is_finite() and ov==ev,'Source value does not equal independently read expected value')
        except Exception as exc:
            result='fail';error=str(exc);errors.append(ref['reference_id']+': '+error)
        if comparisons is not None:
            comparisons.append(dict(reference_id=ref['reference_id'],source=ref['source'],artifact_id=ref['artifact_id'],artifact_sha256=ref['artifact_sha256'],locator=ref['locator'],dimensions=json.dumps(ref['dimensions'],sort_keys=True),vintage=ref['vintage'],expected_value=ref['expected_value'],observed_value=observed,unit=ref['expected_unit'],tolerance=ref['tolerance'],status=result,error=error))
    require(not errors,'; '.join(errors))
    return f'{len(refs)} independently authored observations agree exactly; no production parser or cross-vintage API comparison used.'

def check_secrets():
    reg=read('test/fixtures/config/source_registry.json');access=reg['api_access']
    require(access['environment_variable']=='USDA_FAS_API_KEY' and access['status']=='deferred_without_credentials' and access['dependent_phases']==['04','05'],'API dependency was hidden or incorrectly marked verified')
    require('not_performed' in access['response_verification'],'Unjustified API verification claim')
    patterns=[re.compile(rb'USDA_FAS_API_KEY\s*[=:]\s*[\"\x27]([A-Za-z0-9_+/-]{16,})[\"\x27]'),re.compile(rb'(?i)X-Api-Key[\"\x27]?\s*:\s*[\"\x27]([A-Za-z0-9_+/-]{16,})[\"\x27]'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    actual=os.environ.get('USDA_FAS_API_KEY','').encode();count=0
    for folder in ['config','docs','scripts','test/fixtures','test/tools']:
        for p in path(folder).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
            raw=p.read_bytes();count+=1
            require(not any(pattern.search(raw) for pattern in patterns),f'Possible credential in {p.relative_to(ROOT)} (value redacted)')
            if actual:require(actual not in raw,f'Environment credential found in {p.relative_to(ROOT)} (value redacted)')
    return f'{count} delivered files scanned for credential assignments/private keys and any supplied environment secret; no matches. Authenticated API checks remain deferred.'

CHECKS=[('P00-A1',check_scope),('P00-A2',check_sources),('P00-A3',check_publications),('P00-A4',check_artifacts),('P00-A5',check_references),('P00-A6',check_secrets)]

def live_probe(job):
    result=dict(job,executed_at_utc=datetime.now(timezone.utc).isoformat())
    try:
        require(official(job['url']),'Nonofficial live URL')
        req=urllib.request.Request(job['url'],headers={'User-Agent':'Mozilla/5.0 (compatible; USDA-source-verification/1.0)'})
        with urllib.request.urlopen(req,timeout=50) as response:
            raw=response.read(20_000_001)
            require(len(raw)<=20_000_000,'Live evidence exceeds 20 MB bound')
            result.update(http_status=response.status,final_url=response.url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        require(response.status==200 and raw,'Empty/non-successful live evidence')
        kind=job['format']
        if kind=='pdf':require(raw.startswith(b'%PDF-'),'Live PDF is not a PDF')
        elif kind=='xml':require(ET.fromstring(raw).tag=='Report','Live XML is not WASDE')
        elif kind=='zip':require(zipfile.is_zipfile(io.BytesIO(raw)),'Live ZIP signature invalid')
        elif kind=='csv':require('Value' in next(csv.reader(io.StringIO(raw.decode('utf-8-sig')))),'Live CSV signature invalid')
        elif kind=='json':require(bool(json.loads(raw)),'Empty JSON discovery')
        elif kind=='html':require(job['identity'].lower() in raw.decode('utf-8','replace').lower(),'Wrong live landing document')
        result.update(status='pass',matches_frozen_bytes=result['sha256']==job['frozen_sha256'])
        return result,raw
    except Exception as exc:
        # Store no headers, credential values, request repr or response error text.
        result.update(status='blocked' if isinstance(exc,(urllib.error.URLError,TimeoutError,OSError)) else 'fail',error_type=type(exc).__name__)
        if isinstance(exc,urllib.error.HTTPError):result['http_status']=exc.code
        return result,b''

def live_checks(out):
    cat=read('test/fixtures/catalog.json');jobs=[]
    for a in cat['artifacts']:
        if a['role']=='holdout':jobs.append(dict(id=a['artifact_id'],test_id='P00-A4',url=a['url'],format=Path(a['path']).suffix[1:],frozen_sha256=a['sha256'],frozen_path=a['path']))
    for file,fmt,identity in [('wasde.html','html','WASDE'),('ers.html','html','Commodity Costs'),('rma.html','html','Coverage Level'),('swagger.json','json',''),('fas-circular-inventory.json','json',''),('esr-program-cdn.html','html','Weekly Reporting')]:
        a=read(DISC+file+'.acquisition.json')
        jobs.append(dict(id=file,test_id='P00-A2',url=a['url'],format=fmt,identity=identity,frozen_sha256=a['sha256'],frozen_path=a['path']))
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rec,raw in pool.map(live_probe,jobs):
            if raw:
                if rec['matches_frozen_bytes']:rec['evidence_path']=rec['frozen_path']
                else:
                    p=out/'live_responses'/f"{rec['id']}.{rec['sha256'][:16]}.raw";p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
                    rec['evidence_path']=str(p.relative_to(ROOT))
            records.append(rec)
    (out/'live_checks.json').write_text(json.dumps(records,indent=2)+'\n')
    return records

def version():
    try:git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):git='unavailable'
    h=hashlib.sha256();files=[]
    for directory in ['scripts','config','docs']:
        files.extend(p for p in path(directory).rglob('*') if p.is_file() and p.suffix in {'.py','.json','.md'} and p.name!='execution_status.md')
    files.extend([path('test/fixtures/catalog.json'),path('test/fixtures/references/observations.json'),path('test/fixtures/references/README.md')])
    for p in sorted(files):
        h.update(str(p.relative_to(ROOT)).encode()+b'\0'+p.read_bytes()+b'\0')
    return dict(git_revision=git,source_tree_sha256=h.hexdigest(),scope='scripts, config, stable docs, fixture catalog and independent references; raw bytes are pinned in catalog; mutable execution ledger/results excluded')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',required=True,choices=['offline','live'])
    parser.add_argument('--evidence-dir',required=True)
    args=parser.parse_args();out=path(args.evidence_dir);out.mkdir(parents=True,exist_ok=True)
    code=version();config_hash=digest(path('test/fixtures/config/scope.json'));stamp=datetime.now(timezone.utc).isoformat()
    rows=[];comparisons=[]
    for test_id,check in CHECKS:
        try:
            observed=check(comparisons) if test_id=='P00-A5' else check()
            status='pass'
        except Exception as exc:observed=f'{type(exc).__name__}: {exc}';status='fail'
        rows.append(dict(phase_id='00',test_id=test_id,mode=args.mode,status=status,observed_result=observed,expected_result=EXPECTED[test_id],evidence_path=args.evidence_dir,code_version=code,configuration_hash=config_hash,executed_at_utc=stamp))
    live=[]
    if args.mode=='live':
        live=live_checks(out)
        for row in rows:
            related=[x for x in live if x['test_id']==row['test_id']]
            if related:
                states={x['status'] for x in related}
                if 'fail' in states:row['status']='fail'
                elif 'blocked' in states and row['status']!='fail':row['status']='blocked'
                row['observed_result']+=f' Live probes: {sum(x["status"]=="pass" for x in related)}/{len(related)} successful; see live_checks.json.'
    (out/f'results.{args.mode}.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/f'source_checks.{args.mode}.csv').parent.mkdir(parents=True,exist_ok=True)
    if comparisons:
        with (out/f'source_checks.{args.mode}.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(comparisons[0]));writer.writeheader();writer.writerows(comparisons)
        (out/'source_checks.csv').write_bytes((out/f'source_checks.{args.mode}.csv').read_bytes())
    # Re-scan after writing network evidence and comparisons.
    try:check_secrets()
    except Exception as exc:
        rows[-1]['status']='fail';rows[-1]['observed_result']=str(exc)
        (out/f'results.{args.mode}.json').write_text(json.dumps(rows,indent=2)+'\n')
    modes={}
    for mode in ['offline','live']:
        p=out/f'results.{mode}.json'
        if p.exists():modes[mode]=json.loads(p.read_text())
    combined=[]
    for test_id,_ in CHECKS:
        relevant=[next(r for r in rs if r['test_id']==test_id) for rs in modes.values()]
        row=dict(next(r for r in rows if r['test_id']==test_id));row['mode']='combined'
        fresh=all(r['configuration_hash']==config_hash and r['code_version']==code for r in relevant)
        states={r['status'] for r in relevant}
        row['status']='fail' if 'fail' in states else 'blocked' if len(modes)!=2 or not fresh or 'blocked' in states else 'pass'
        row['observed_result']='; '.join(f"{r['mode']}: {r['observed_result']}" for r in relevant)
        if len(modes)!=2 or not fresh:row['observed_result']+='; both modes with matching code/configuration are required.'
        row['mode_evidence']={mode:str((out/f'results.{mode}.json').relative_to(ROOT)) for mode in modes}
        combined.append(row)
    (out/'results.json').write_text(json.dumps(combined,indent=2)+'\n')
    exit_code=0 if all(r['status']=='pass' for r in rows) else 1
    command=shlex.join(['python3','test/tools/verify_phase00.py','--mode',args.mode,'--evidence-dir',args.evidence_dir])
    with (out/'commands.txt').open('a') as f:
        f.write(f'\nUTC: {stamp}\nWorking directory: {ROOT}\nCommand: {command}\nInterpreter: {sys.executable}\nExit code: {exit_code}\n')
    for row in rows:print(f"{row['test_id']} [{args.mode}] {row['status']}: {row['observed_result']}")
    print('Phase gate: '+('passed' if all(r['status']=='pass' for r in combined) else 'not passed; inspect results.json'))
    return exit_code

if __name__=='__main__':sys.exit(main())
