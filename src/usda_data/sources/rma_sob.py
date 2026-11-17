"""RMA coverage-level SOB: complete 28-field source records and annual streaming."""
from datetime import datetime
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urljoin
import csv,io,json,re,zipfile
from bs4 import BeautifulSoup
from pypdf import PdfReader
from ..schema import Field,Schema
from ..storage import Store,atomic_write,canonical,sha256
from ..http import HTTPClient
from ..config import HTTPConfig
from ..errors import ConfigurationError,FormatError,ValidationError

LANDING='https://www.rma.usda.gov/tools-reports/summary-of-business/state-county-crop-summary-business'
PARSER_VERSION='rma-sob-2'
COLUMNS=['commodity_year','state_code','state_abbreviation','county_code','county_name','commodity_code','commodity_name','insurance_plan_code','insurance_plan_name','coverage_category','delivery_type','coverage_level','policies_sold','policies_earning_premium','policies_indemnified','units_earning_premium','units_indemnified','quantity_type','net_reported_quantity','endorsed_companion_acres','liability_amount','total_premium','subsidy_amount','state_private_subsidy','additional_subsidy','efa_premium_discount','indemnity_amount','loss_ratio']
KEYS=COLUMNS[:12]+['quantity_type']
INTEGER_FIELDS=COLUMNS[12:17]+COLUMNS[18:27]
MONEY=COLUMNS[20:27]
fields=[]
for i,name in enumerate(COLUMNS):
    kind='decimal' if name in {'coverage_level','loss_ratio'} else 'integer' if name in INTEGER_FIELDS else 'string'
    fields.append(Field(name,kind,name not in KEYS,name.replace('_',' '),f'Official 1989-forward SOB coverage-level field {i+1}','USD' if name in MONEY else 'source quantity_type' if name=='net_reported_quantity' else 'Acres' if name=='endorsed_companion_acres' else 'ratio' if kind=='decimal' else 'count' if name in INTEGER_FIELDS else 'not_applicable',key=name in KEYS))
fields += [Field('raw_record','string',False,'Original pipe row excluding terminator; source NUL is encoded as literal Unicode escape for SQL portability; exact bytes remain in raw archive','raw source'),Field('missing_fields','string',False,'Explicit missing-value field list; zeros stay zero','blank numeric fields'),Field('count_availability','string',False,'CLIP counts unavailable per official layout; source raw values remain','layout CLIP note'),Field('source_member','string',False,'Original ZIP member','ZIP directory'),Field('source_line','integer',False,'One-based source line locator, not a key','raw text record'),Field('source_release_date','date',True,'Publication day unknown; Last-Modified is transport metadata','source does not provide date'),Field('source_release_at_utc','datetime',True,'Unknown exact source release time','source metadata'),Field('release_time_precision','string',False,'unknown','source metadata'),Field('retrieved_at_utc','datetime',False,'UTC artifact capture time','receipt'),Field('source_artifact_id','string',False,'Exact ZIP bytes SHA256','raw storage'),Field('snapshot_id','string',False,'Versioned normalized partition identity','storage manifest'),Field('vintage_type','string',False,'current_revised commodity-year capture','RMA source semantics')]
SCHEMA=Schema('rma_sob','2',tuple(fields))


def years_option(values):
    if isinstance(values,str):
        try:
            if ':' in values:
                a,b=map(int,values.split(':'));values=list(range(a,b+1))
            else:values=[int(v) for v in values.split(',')]
        except ValueError:raise ConfigurationError('Commodity years require YYYY,YYYY or YYYY:YYYY') from None
    else:values=list(values)
    if not values or any(type(v) is not int or v<1989 or v>2200 for v in values):raise ConfigurationError('RMA coverage-level supported commodity years start at 1989; 1948-1988 is an unsupported separate layout')
    return sorted(set(values))


def fetch(client,store,url,kind,refresh=False):
    cache=store.root/'manifests/rma-sob/urls'/f'{sha256(url.encode())}.json'
    if cache.exists() and not refresh:
        r=json.loads(cache.read_text());return store.artifact(r['source_artifact_id']),r
    body,meta=client.get(url,expected=kind);receipt=store.raw(body,metadata=meta)
    if cache.exists():
        prior=json.loads(cache.read_text())
        if prior['source_artifact_id']==receipt['source_artifact_id']:receipt=prior
    atomic_write(cache,canonical(receipt));return store.artifact(receipt['source_artifact_id']),receipt


def discover(client,store,*,refresh=False):
    path,r=fetch(client,store,LANDING,'html',refresh)
    soup=BeautifulSoup(path.read_bytes(),'html.parser');files={};layouts=[];unsupported=[]
    for a in soup.find_all('a',href=True):
        url=urljoin(LANDING,a['href'])
        m=re.search(r'/sobcov_(\d{4})\.zip$',url,re.I)
        if m:files[int(m[1])]=url
        if 'SOB_State_County_Crop_with_Coverage_Level_1989_Forward.pdf' in url:layouts.append(url)
        if '1948_1988' in url:unsupported.append(url)
    if not files or len(set(layouts))!=1:raise FormatError('RMA discovery lacks coverage-level files or unambiguous official layout')
    layout_path,layout_receipt=fetch(client,store,layouts[0],'pdf',refresh)
    text=' '.join(p.extract_text() or '' for p in PdfReader(layout_path).pages)
    flat=re.sub(r'\s+',' ',text)
    for phrase in ['1989','Quantity Type','Coverage Level','EFA Premium Discount','Loss Ratio']:
        if phrase.replace(' ','') not in flat.replace(' ',''):raise FormatError('Unknown RMA layout definition')
    result={'years':{str(y):u for y,u in sorted(files.items())},'layout_url':layouts[0],'layout_artifact_id':layout_receipt['source_artifact_id'],'layout_version':'28-fields-1989-forward','supported_start_year':1989,'unsupported_history':{'period':'1948-1988','reason':'Distinct State/County/Commodity layout does not supply this product coverage-level grain','source_links':unsupported},'discovery_artifact_id':r['source_artifact_id']}
    atomic_write(store.root/'manifests/rma-sob/discovery.json',canonical(result))
    return result


def normalize(row,receipt,year,member,line):
    if len(row)!=28:raise FormatError(f'RMA row width is {len(row)}, expected 28')
    source=[v.strip() for v in row];record={}
    if source[0]!=str(year):raise ValidationError('RMA source commodity year does not match requested partition')
    for index,width in [(0,4),(1,2),(3,3),(5,4),(7,2)]:
        if not re.fullmatch(r'\d{'+str(width)+'}',source[index]):raise ValidationError('RMA code lost width/leading zeros or contains unknown characters')
    if source[9] not in {'A','C','E','L'} or source[10] not in {'RCAT','RBUP','FCAT','FBUP'}:raise ValidationError('Unknown RMA coverage/delivery category')
    clip=source[8].upper()=='CLIP'
    for name,value in zip(COLUMNS,source):
        if clip and name in COLUMNS[12:17]:
            if value not in {'','\x00'} and not value.isdigit():raise FormatError('Unknown CLIP unavailable-count marker')
            record[name]=None;continue
        if name in INTEGER_FIELDS:
            if value=='':record[name]=None
            elif re.fullmatch(r'-?\d+',value):
                number=int(value)
                if number<0 and name!='indemnity_amount':raise ValidationError('Signed value in an unsigned RMA layout field')
                record[name]=number
            else:raise FormatError('Unknown RMA integer/quantity representation')
        elif name in {'coverage_level','loss_ratio'}:
            if not value and name=='loss_ratio':record[name]=None
            else:
                try:record[name]=Decimal(value)
                except InvalidOperation:raise FormatError('Unknown RMA decimal representation') from None
                if not record[name].is_finite():raise FormatError('Nonfinite RMA decimal')
        else:record[name]=value
    if not Decimal(0)<=record['coverage_level']<=Decimal(1):raise ValidationError('RMA coverage level outside [0,1]')
    if not all(record[k] is not None and str(record[k])!='' for k in KEYS):raise ValidationError('Missing RMA grouping dimension')
    clip=record['insurance_plan_name'].strip().upper()=='CLIP'
    if clip:
        for name in COLUMNS[12:17]:record[name]=None
    missing=[n for n in COLUMNS if record[n] is None]
    record.update(raw_record='|'.join(row).replace('\x00','\\u0000'),missing_fields=json.dumps(missing),count_availability='unavailable_CLIP_per_layout' if clip else 'reported_source_values',source_member=member,source_line=line,source_release_date=None,source_release_at_utc=None,release_time_precision='unknown',retrieved_at_utc=datetime.fromisoformat(receipt['retrieved_at_utc']),source_artifact_id=receipt['source_artifact_id'],snapshot_id='unpublished',vintage_type='current_revised')
    return record


def iter_parse(path,receipt,year,*,chunk_size=5000,accounting=None):
    if type(chunk_size) is not int or chunk_size<1:raise ConfigurationError('RMA chunk size must be positive')
    years_option([year]);accounting=accounting if accounting is not None else {};accounting.update(input_rows=0,mapped_rows=0,quarantined_rows=0,quantity_types={},members=[],missing_counts={})
    records=[]
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist()
        if not infos:raise FormatError('Empty RMA ZIP')
        for info in infos:
            if info.filename.startswith('/') or '..' in Path(info.filename).parts or not re.fullmatch(r'sobcov_?(?:\d{2}|\d{4})\.txt',Path(info.filename).name,re.I) or info.file_size>1_000_000_000:
                raise FormatError('Unknown or unsafe RMA ZIP data member')
            accounting['members'].append(info.filename)
            with io.TextIOWrapper(archive.open(info),encoding='utf-8-sig',newline='') as stream:
                for line,row in enumerate(csv.reader(stream,delimiter='|',strict=True),1):
                    accounting['input_rows']+=1
                    try:r=normalize(row,receipt,year,info.filename,line)
                    except (FormatError,ValidationError):accounting['quarantined_rows']+=1;raise
                    records.append(r);accounting['mapped_rows']+=1
                    kind=r['quantity_type'];accounting['quantity_types'][kind]=accounting['quantity_types'].get(kind,0)+1
                    for name in json.loads(r['missing_fields']):accounting['missing_counts'][name]=accounting['missing_counts'].get(name,0)+1
                    if len(records)==chunk_size:yield SCHEMA.frame(records);records=[]
    if records:yield SCHEMA.frame(records)
    if accounting['input_rows']!=accounting['mapped_rows']:raise ValidationError('RMA source row accounting mismatch')


def iter_download(commodity_years,*,data_dir='data',refresh=False,chunk_size=5000,all_history=False,client=None):
    """Yield exact-schema chunks; annual version publication completes before exposure.

    Raw ZIP/layout artifacts and full annual snapshots are retained. Global key
    validation uses a disk-backed table, keeping memory bounded by chunk_size.
    all_history covers discovered 1989-forward files and reports unsupported older
    layouts explicitly; it does not imply 1948-1988 coverage.
    """
    store=Store(data_dir);owned=client is None;client=client or HTTPClient(HTTPConfig(trust_environment=False))
    try:
        discovery_path=store.root/'manifests/rma-sob/discovery.json'
        inventory=discover(client,store,refresh=refresh) if refresh or not discovery_path.exists() else json.loads(discovery_path.read_text())
        years=sorted(map(int,inventory['years'])) if all_history else years_option(commodity_years)
        for year in years:
            if str(year) not in inventory['years']:raise ValidationError('Requested RMA year absent from official discovery; no unavailable-history claim is inferred')
            path,receipt=fetch(client,store,inventory['years'][str(year)],'zip',refresh)
            accounting={}
            try:
                manifest=store.publish_stream('rma-sob',str(year),iter_parse(path,receipt,year,chunk_size=chunk_size,accounting=accounting),SCHEMA,[receipt['source_artifact_id'],inventory['layout_artifact_id']],parser_version=PARSER_VERSION,configuration={'commodity_year':str(year),'layout':'28-fields-1989-forward'})
            finally:atomic_write(store.root/'manifests/rma-sob/accounting'/f'{year}-{receipt["source_artifact_id"]}.json',canonical(accounting))
            yield from SCHEMA.read_csv_chunks(store.root/manifest['csv_path'],chunk_size)
    finally:
        if owned:client.close()
