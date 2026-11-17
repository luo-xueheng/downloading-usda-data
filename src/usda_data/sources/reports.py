"""Discover, archive and parse FAS circulars with explicit report-date precision."""
from datetime import date,datetime
import io,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from .report_tables import SCHEMA,parse_report,report_period
from .fas_common import client_config
from ..http import HTTPClient
from ..storage import Store,atomic_write,canonical,sha256
from ..errors import ConfigurationError,DownloadError,AuthenticationError,FormatError,ValidationError

DIRECTORY='https://apps.fas.usda.gov/psdonline/CircularsHandler.ashx'
FAMILIES={'world-production':('production','World Agricultural Production','world-agricultural-production'),'grain-trade':('Grain','Grain: World Markets and Trade','grain-world-markets-and-trade'),'oilseed-trade':('Oilseeds','Oilseeds: World Markets and Trade','oilseeds-world-markets-and-trade')}
PARSER_VERSION='fas-reports-4-'+sha256(Path(__file__).read_bytes()+Path(__file__).with_name('report_tables.py').read_bytes()+Path(__file__).with_name('report_dimension_repairs.json').read_bytes()+Path(__file__).with_name('report_source_gaps.json').read_bytes())
ARTICLES=json.loads(Path(__file__).with_name('report_article_inventory.json').read_text())


def bounds(start,end):
    try:a=date.fromisoformat(str(start));b=date.fromisoformat(str(end))
    except ValueError:raise ConfigurationError('Report bounds require YYYY-MM-DD publication dates') from None
    if a>b:raise ConfigurationError('Report start follows end')
    return a,b


def fetch_public(client,store,url,expected,*,refresh=False):
    cache=store.root/'manifests/reports/urls'/f'{sha256(url.encode())}.json'
    if cache.exists() and not refresh:
        r=json.loads(cache.read_text());return store.artifact(r['source_artifact_id']).read_bytes(),r
    body,meta=client.get(url,expected=expected);r=store.raw(body,metadata=meta)
    if cache.exists():
        prior=json.loads(cache.read_text())
        if prior['source_artifact_id']==r['source_artifact_id']:r=prior
    atomic_write(cache,canonical(r));return body,r


def discover(report_family,start,end,*,store,client,refresh=False):
    if report_family not in FAMILIES:raise ConfigurationError('Unknown report family')
    start,end=bounds(start,end);body,receipt=fetch_public(client,store,DIRECTORY,'json',refresh=refresh)
    obj=json.loads(body)
    if set(obj)!={'DownloadPath','CircularSets'}:raise FormatError('Unknown FAS report directory layout')
    code,title,slug=FAMILIES[report_family];candidates=[]
    for year in obj['CircularSets']:
        if set(year)!={'CalendarYear','Months'}:raise FormatError('Unknown report year inventory')
        for month in year['Months']:
            period=f'{int(year["CalendarYear"]):04}-{int(month["Item1"]):02}'
            if start.strftime('%Y-%m')<=period<=end.strftime('%Y-%m'):
                candidates.append({'report_family':report_family,'report_period':period,'title':title,'url':f'https://apps.fas.usda.gov/PSDOnline/Circulars/{period[:4]}/{period[-2:]}/{code}.pdf','discovery_artifact_id':receipt['source_artifact_id'],'source_release_date':None,'source_release_at_utc':None,'release_time_precision':'month','status':'discovered_not_fetched'})
    atomic_write(store.root/'manifests/reports/discovery'/f'{report_family}-{start}-{end}.json',canonical({'candidates':candidates,'requested_start':str(start),'requested_end':str(end),'directory_artifact':receipt['source_artifact_id'],'coverage_policy':'Directory months are candidates, not proof each family exists; unlisted months remain unresolved until independently evidenced.'}))
    return sorted(candidates,key=lambda r:r['report_period'])


def resolve_attachment(client,store,record,*,refresh=False):
    """Resolve a missing or misdated circular through USDA NAL's dated archive."""
    original=record['url']
    resolved=store.root/'manifests/reports/resolved'/f'{sha256(original.encode())}.json'
    if resolved.exists() and not refresh:
        saved=json.loads(resolved.read_text())
        if saved['record']['report_period']!=record['report_period']:raise ValidationError('Cached alternate report period differs')
        return store.artifact(saved['receipt']['source_artifact_id']).read_bytes(),saved['receipt'],{**record,**saved['record']}
    try:
        body,receipt=fetch_public(client,store,original,'pdf',refresh=refresh)
        with pdfplumber.open(io.BytesIO(body)) as pdf:
            if report_period(pdf)!=record['report_period']:
                raise ValidationError('Original circular URL serves a different report month')
        return body,receipt,record
    except (DownloadError,ValidationError,FormatError) as exc:
        original_error=str(exc)
    slug=FAMILIES[record['report_family']][2]
    url=f'https://esmis.nal.usda.gov/publication/{slug}?date={record["report_period"]}'
    html,inventory=fetch_public(client,store,url,'html',refresh=refresh)
    soup=BeautifulSoup(html,'html.parser');candidates={}
    for a in soup.find_all('a',href=True):
        if '/release-files/' not in a['href']:continue
        label=a.get_text(' ',strip=True)
        try:published=datetime.strptime(label,'%b %d %Y - pdf').date()
        except ValueError:continue
        if published.strftime('%Y-%m')==record['report_period']:
            candidates[urljoin(url,a['href'])]=published
    if len(candidates)!=1:
        raise ValidationError('Official alternate archive does not identify exactly one matching report; original error: '+original_error)
    alternative,published=next(iter(candidates.items()))
    body,receipt=fetch_public(client,store,alternative,'pdf',refresh=refresh)
    with pdfplumber.open(io.BytesIO(body)) as pdf:
        if report_period(pdf)!=record['report_period']:
            raise ValidationError('Alternate official attachment also has mismatched embedded month')
    record={**record,'url':alternative,'original_url':original,'original_error':original_error,
            'release_evidence_url':url,'release_evidence_artifact_id':inventory['source_artifact_id'],
            'source_release_date':published.isoformat(),'source_release_at_utc':None,'release_time_precision':'day'}
    atomic_write(resolved,canonical({'record':record,'receipt':receipt}))
    return body,receipt,record


def known_release_evidence(client,store,record,*,refresh=False):
    """Read dated official article links when available; never assume a schedule date.

    The embedded PDF generally gives a month. Date filtering within a partial month
    requires independent article metadata; an unknown date cannot silently pass.
    """
    family=record['report_family'];period=record['report_period'];slug=FAMILIES[family][2]
    # Search-page links are discovery evidence only. Date strings in links are
    # not publication proof until the corresponding article metadata is checked.
    known=ARTICLES.get(family,{}).get(period)
    landing=known['url'] if known else 'https://www.fas.usda.gov/data/'+slug
    try:body,landing_receipt=fetch_public(client,store,landing,'html',refresh=refresh)
    except (DownloadError,AuthenticationError):
        search='https://www.fas.usda.gov/data/search?keyword='+slug.replace('-','%20')
        try:body,landing_receipt=fetch_public(client,store,search,'html',refresh=refresh)
        except (DownloadError,AuthenticationError):return record
    soup=BeautifulSoup(body,'html.parser')
    options=[]
    if soup.select_one('.c-page-title__meta time') and soup.find('h1'):
        options.append((landing,body,landing_receipt))
    for a in soup.find_all('a',href=True):
        if a.get_text(' ',strip=True)!=FAMILIES[family][1]:continue
        m=re.search(r'-(\d{2})(\d{2})(\d{4})$',a['href'])
        if m and f'{m[3]}-{m[1]}'==period:
            url=urljoin(landing,a['href'])
            article,article_receipt=fetch_public(client,store,url,'html',refresh=refresh)
            options.append((url,article,article_receipt))
    for url,article,article_receipt in options:
        parsed=BeautifulSoup(article,'html.parser');h1=parsed.find('h1');clock=parsed.select_one('.c-page-title__meta time')
        if not h1 or h1.get_text(' ',strip=True)!=FAMILIES[family][1] or not clock:continue
        instant=datetime.fromisoformat(clock['datetime'].replace('Z','+00:00'))
        if instant.strftime('%Y-%m')!=period:continue
        return {**record,'source_release_date':instant.date().isoformat(),'source_release_at_utc':instant.isoformat(),'release_time_precision':'timestamp','release_evidence_artifact_id':article_receipt['source_artifact_id'],'release_evidence_url':url}
    return record


def iter_reports(report_family,start,end,*,data_dir='data',refresh=False,client=None):
    """Yield verified PDF manifest records; raw bytes, revisions and attachments persist."""
    start,end=bounds(start,end);store=Store(data_dir);owned=client is None;client=client or HTTPClient(client_config())
    try:
        candidates=discover(report_family,start,end,store=store,client=client,refresh=refresh)
        for record in candidates:
            body,receipt,record=resolve_attachment(client,store,record,refresh=refresh)
            with pdfplumber.open(io.BytesIO(body)) as pdf:
                actual=report_period(pdf)
                first=pdf.pages[0].extract_text(x_tolerance=1,y_tolerance=3) or ''
                if actual!=record['report_period']:raise ValidationError('Report filename month does not match embedded report date')
                # First-page mastheads may split words/lines; validate family by its distinctive terms.
                terms={'world-production':['World','Agricultural','Production'],'grain-trade':['Grain:','Markets','Trade'],'oilseed-trade':['Oilseeds:','Markets','Trade']}[report_family]
                if not ('not published' in first and 'lapse in' in first) and not all(t.replace(' ','') in re.sub(r'\s+','',first) for t in terms):
                    marker={'world-production':'Wheat Area, Yield, and Production','grain-trade':'All Grain Summary Comparison','oilseed-trade':'Major Oilseeds: World Supply and Distribution'}[report_family]
                    found=any(marker in (p.extract_text(x_tolerance=1,y_tolerance=3) or '') for p in pdf.pages[1:])
                    if not found:raise ValidationError('Wrong report family attachment; neither masthead nor mandatory family table marker found')
            if not record.get('release_evidence_artifact_id'):record=known_release_evidence(client,store,record,refresh=refresh)
            if record['source_release_date']:
                if not start<=date.fromisoformat(record['source_release_date'])<=end:continue
            else:
                import calendar
                month_start=date.fromisoformat(record['report_period']+'-01');month_end=month_start.replace(day=calendar.monthrange(month_start.year,month_start.month)[1])
                if start>month_start or end<month_end:raise ValidationError('Partial-month report filtering requires a verified publication date; only month precision is available')
            destination=store.root/'reports'/report_family/record['report_period']/receipt['source_artifact_id']/'report.pdf'
            if not destination.exists():atomic_write(destination,body)
            record={**record,'status':'download_verified','source_artifact_id':receipt['source_artifact_id'],'retrieved_at_utc':receipt['retrieved_at_utc'],'bytes':len(body),'attachment_path':str(destination.relative_to(store.root))}
            atomic_write(destination.parent/'manifest.json',canonical(record))
            yield record
    finally:
        if owned:client.close()


def download_reports(report_family,start,end,*,data_dir='data',refresh=False):
    """Return report manifests and preserve verified PDF attachments and revisions.

    Date bounds are inclusive. Exact dates use official article metadata; otherwise
    a full requested month is required and publication precision remains month.
    Empty/missing directory months are not claimed to be permanently unavailable.
    """
    return pd.DataFrame(list(iter_reports(report_family,start,end,data_dir=data_dir,refresh=refresh)),dtype=object)


def iter_structured_reports(report_family,start,end,*,data_dir='data',refresh=False,client=None):
    store=Store(data_dir)
    for record in iter_reports(report_family,start,end,data_dir=data_dir,refresh=refresh,client=client):
        body=store.artifact(record['source_artifact_id']).read_bytes()
        release=date.fromisoformat(record['source_release_date']) if record['source_release_date'] else None
        backfill_version=sha256(b''.join(Path(__file__).with_name(name).read_bytes() for name in ['report_tables.py','report_dimension_repairs.json','report_source_gaps.json','reports.py']))
        cached_coverage=store.root/'manifests/reports/backfill_coverage'/f'{report_family}-{record["report_period"]}-{backfill_version}.json'
        cached=store.latest(report_family+'-reports-backfill',record['report_period'])
        if cached and cached['parser_version']=='report-source-'+backfill_version and cached['source_artifact_ids']==[record['source_artifact_id']] and cached_coverage.exists():
            frame=SCHEMA.read_csv(store.root/cached['csv_path']);evidence=json.loads(cached_coverage.read_text())
            frame['source_release_date']=release;frame['release_time_precision']='day' if release else 'month'
        else:
            frame,evidence=parse_report(body,report_family,record,expected_period=record['report_period'],release_date=release)
        if record['source_release_at_utc']:
            frame['source_release_at_utc']=datetime.fromisoformat(record['source_release_at_utc']);frame['release_time_precision']='timestamp'
        artifacts=[record['source_artifact_id']]
        if record.get('release_evidence_artifact_id'):artifacts.append(record['release_evidence_artifact_id'])
        snapshot=store.publish(report_family+'-reports',record['report_period'],frame,SCHEMA,artifacts,parser_version=PARSER_VERSION,configuration={'report_family':report_family,'supported_layout':'verified numbered and changes tables'})
        atomic_write(store.root/'manifests/reports/coverage'/f'{report_family}-{record["report_period"]}-{snapshot["snapshot_id"]}.json',canonical(evidence))
        yield SCHEMA.read_csv(store.root/snapshot['csv_path'])
