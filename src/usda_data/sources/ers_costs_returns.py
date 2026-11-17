"""ERS recent, historical and forecast observations with distinct source methods."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import csv
import io
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
import zipfile
import openpyxl
import xlrd
from bs4 import BeautifulSoup
from ..schema import Field, Schema
from ..errors import ConfigurationError, FormatError, ValidationError
from ..http import HTTPClient
from ..storage import Store, atomic_write, canonical, sha256

LANDING='https://www.ers.usda.gov/data-products/commodity-costs-and-returns'
PARSER_VERSION='ers-1'
RECENT_COLUMNS=['Commodity','Category','Item','Units','Size','Region','Country','Year','Value','Survey base year']
FORECAST_COLUMNS=['Commodity','Category','Item','Units','Region','Year','Value']
XLSX_RECENT=['Commodity','Category','Item','Item2','Units','Size','Region','Country','Year','Value','Survey base year','Note']
XLSX_BEETS=['Commodity','CommodityId','Category','CategoryId','Item','Item2','ItemId','Units','UnitsAbr','UnitsId','Region','RegionId','Country','CountryId','Year','Value','SurveyBaseYear','Note','Order','Size','SizeId']
KEYS=['commodity','enterprise_type','region','country','size','year_label','series_family','methodology','table_title','category','item','unit','forecast_vintage','classification']
SCHEMA=Schema('ers_costs_returns','1',tuple([Field(k,'string',False,k.replace('_',' '),'official field or source table metadata',key=True) for k in KEYS]+[
 Field('year','integer',False,'Observation year; original label retained','Year/year header'),Field('value','decimal',True,'Exact stored source value, no rounding or floating-point aggregation','Value/cell','unit column'),Field('raw_value','string',False,'Source lexical or BIFF stored numeric representation','source cell'),Field('value_status','string',False,'reported/missing/unavailable/suppressed/not_applicable','source marker'),Field('estimate_status','string',False,'Only explicit source statuses; otherwise unknown','year suffix/forecast source'),Field('source_item','string',False,'Unmodified source item text','Item/row label'),Field('source_extra','string',False,'Original additional source fields, codes and notes','source record'),Field('source_locator','string',False,'CSV record or sheet/cell locator; not a business key','source position'),Field('source_release_date','date',True,'Official last-update date if provided; historical forecast month is not an exact date','landing page'),Field('source_release_at_utc','datetime',True,'Unknown precise release time stays null','official source'),Field('release_time_precision','string',False,'date or unknown','source metadata'),Field('retrieved_at_utc','datetime',False,'UTC retrieval time','acquisition receipt'),Field('source_artifact_id','string',False,'Original file/ZIP SHA256','raw archive'),Field('snapshot_id','string',False,'Parser/schema/config version identity','normalized snapshot'),Field('vintage_type','string',False,'current_revised or forecast_vintage','source family')]))


def slug(value):
    return re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')


def discover_page(body, url=LANDING):
    """Account for every linked product file; prefer CSV over duplicate presentations."""
    soup=BeautifulSoup(body,'html.parser');records=[];section=None
    for node in soup.find_all(['h3','a']):
        text=node.get_text(' ',strip=True)
        if node.name=='h3':
            if text=='Recent Cost and Returns':section=('Recent',None)
            elif text=='Cost-of-Production Forecasts':section=('forecast',None)
            elif text.startswith('Historical Costs and Returns:'):section=('Historical',text.split(':',1)[1].strip())
            continue
        href=node.get('href','');extension=Path(urlsplit(href).path).suffix.lower()
        if '/media/' not in href or extension not in {'.csv','.xlsx','.xls','.zip'}:
            continue
        if section is None:
            raise FormatError('ERS download outside a recognized product section')
        parent=node.find_parent('div',class_='usa-collection__body')
        if parent is None or parent.find('h3') is None:
            raise FormatError('Unknown ERS download-card layout')
        label=parent.find('h3').get_text(' ',strip=True);family,commodity=section
        if 'Previously Released' in label:family='previously released forecasts'
        release=None;next_update=None
        for time in parent.find_all('time'):
            if 'Last Updated' in time.get_text():release=time.get('datetime')
            if 'Next Update' in time.get_text():next_update=time.get('datetime')
        target=urljoin(url,href)
        if not (urlsplit(target).hostname or '').endswith('ers.usda.gov'):
            raise FormatError('Unexpected ERS attachment host')
        identifier=urlsplit(target).path.split('/')[2]
        sibling_csv=any(Path(urlsplit(a.get('href','')).path).suffix.lower()=='.csv' for a in parent.find_all('a'))
        selected=not(extension=='.xlsx' and sibling_csv)
        records.append({'url':target,'product_id':identifier,'label':label,'commodity_group':commodity or label,'family':family,'format':extension[1:],'source_release_date':release,'next_update_date':next_update,'selected':selected,'reason':'numeric_source' if selected else 'equivalent XLSX presentation; CSV chosen, XLSX layout separately inspected','partition':slug(f'{family}-{commodity or label}-{identifier}')})
    links={urljoin(url,a.get('href')) for a in soup.find_all('a',href=True) if '/media/' in a['href'] and Path(urlsplit(a['href']).path).suffix.lower() in {'.csv','.xls','.xlsx','.zip'}}
    if links!={r['url'] for r in records} or not records:
        raise FormatError('Unaccounted ERS file links')
    return records


def discover(client,store):
    body,meta=client.get(LANDING,expected='html');receipt=store.raw(body,metadata=meta)
    records=discover_page(body)
    for r in records:r['discovery_artifact_id']=receipt['source_artifact_id']
    atomic_write(store.root/'manifests/costs-returns/discovery.json',canonical(records))
    return records


def numeric(value):
    raw='' if value is None else str(value)
    marks={'':'missing',' ':'missing','NA':'unavailable','N/A':'not_applicable','n.a.':'unavailable','(D)':'suppressed','D':'suppressed','--':'unavailable','-':'unavailable','*':'suppressed','1/':'included_elsewhere'}
    if raw.strip() in marks:return None,raw,marks[raw.strip()]
    try:
        result=Decimal(raw.replace(',',''))
        if not result.is_finite():raise InvalidOperation()
    except InvalidOperation:
        raise FormatError('Unknown ERS numeric value/marker') from None
    return result,raw,'reported'


def clean_item(text):
    return re.sub(r'\s+',' ',re.sub(r'\s+\d+/','',str(text))).strip()


def observation(d,meta,receipt,locator, *, member='',table_title='machine readable',extra=None):
    label=str(d['Year']).strip()
    if not re.fullmatch(r'(?:19|20)\d{2}(?:[FfEePp])?',label):
        raise FormatError('Unknown ERS year label')
    year=int(label[:4]);value,raw,status=numeric(d['Value'])
    is_forecast='forecast' in meta['family'].lower()
    commodity=str(d['Commodity']).strip();enterprise=meta['commodity_group'] if commodity.lower().startswith('hogs') else commodity
    release=date.fromisoformat(meta['source_release_date']) if meta.get('source_release_date') else None
    source_item=str(d['Item'])
    record=dict(commodity=commodity,enterprise_type=enterprise,region=str(d['Region']).strip(),country=str(d.get('Country') or 'United States'),size=str(d.get('Size') or 'not_specified'),year_label=label,series_family=meta['family'],methodology=str(d.get('Survey base year') or d.get('SurveyBaseYear') or d.get('methodology') or (table_title if meta['family']=='Historical' else 'source_forecast_method_not_labelled')),table_title=table_title,category=str(d['Category']).strip() or 'not_labelled',item=clean_item(source_item),unit=str(d['Units']).strip(),forecast_vintage=member or ('current_forecast' if is_forecast else 'not_applicable'),classification=str(d.get('classification') or 'not_applicable'),year=year,value=value,raw_value=raw,value_status=status,estimate_status='forecast' if is_forecast or label.endswith(('F','f')) else 'estimate' if label.endswith(('E','e')) else 'unknown',source_item=source_item,source_extra=json.dumps(extra or {},sort_keys=True,default=str),source_locator=json.dumps(locator,sort_keys=True),source_release_date=release,source_release_at_utc=None,release_time_precision='date' if release else 'unknown',retrieved_at_utc=datetime.fromisoformat(receipt['retrieved_at_utc']),source_artifact_id=receipt['source_artifact_id'],snapshot_id='unpublished',vintage_type='forecast_vintage' if is_forecast else 'current_revised')
    if not all(record[k] for k in KEYS):
        raise ValidationError('Missing ERS business dimension')
    return record


def long_rows(rows,columns,meta,receipt, *, sheet=None,member='',accounting):
    if columns not in [RECENT_COLUMNS,FORECAST_COLUMNS,XLSX_RECENT,XLSX_BEETS]:
        raise FormatError('Unauthorized ERS long-form column layout')
    for number,values in enumerate(rows,2):
        if all(v in (None,'') for v in values):
            accounting['excluded'].append({'sheet':sheet,'row':number,'reason':'empty spreadsheet row'});continue
        if len(values)!=len(columns):raise FormatError('ERS row width mismatch')
        d=dict(zip(columns,values))
        if isinstance(d['Year'],(float,int)):
            if int(d['Year'])!=d['Year']:raise FormatError('Nonintegral year')
            d['Year']=str(int(d['Year']))
        locator={'record':number} if not sheet else {'sheet':sheet,'row':number,'column':columns.index('Value')+1}
        if member:locator['member']=member
        accounting['input_data_cells']+=1
        yield observation(d,meta,receipt,locator,member=member,extra={k:v for k,v in d.items() if k not in RECENT_COLUMNS})


def year_cell(value):
    if isinstance(value,(float,int)) and value==int(value):value=str(int(value))
    return str(value).strip() if re.fullmatch(r'(?:19|20)\d{2}[FfEePp]?',str(value).strip()) else None


def table_title_method(title,basis,sheet):
    return f'{title} | {basis} | {sheet}'


def wide_rows(rows,meta,receipt,sheet, *, member='',accounting):
    """Read title/year/units/item sections, retaining each actual table and crop class.

    Each recognized item/year cell, including blanks, is mapped. Numerical cells
    outside a year block or under unlabeled items fail rather than disappear.
    """
    notes=[str(row[0]).strip() for row in rows if row and re.match(r'^\s*(?:\d+/|F\s*=|Note:|Source:|See footnote)',str(row[0] or ''),re.I)]
    title='';years={};unit='';category='not_labelled';classes={};units={};basis='not_labelled';header_indices=set();numeric_mapped=set()
    all_numeric={(r,c) for r,row in enumerate(rows) for c,v in enumerate(row) if isinstance(v,(float,int)) and not isinstance(v,bool)}
    for i,row in enumerate(rows):
        text=str(row[0] or '') if row else '';label=text.strip();nonempty=[str(v).strip() for v in row if v is not None and str(v).strip()]
        if not nonempty:continue
        # Titles precede year headers and contain explicit production-cost wording.
        if re.search(r'(?:costs?|returns).*\b(?:19|20)\d{2}',label,re.I) and not any(isinstance(v,(int,float)) for v in row[1:]):
            unit = unit if title == label else ''
            title=label;years={};category='not_labelled';classes={}
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'table title'});continue
        candidate={c:year_cell(v) for c,v in enumerate(row) if c>0 and year_cell(v)}
        if candidate and ('item' in label.lower() or len(candidate)>=2 and not any(isinstance(v,(int,float)) and c not in candidate for c,v in enumerate(row) if c>0)):
            years=candidate
            header_indices.update((i,c) for c in candidate)
            # Column group labels can be centered. Assign each contiguous year block
            # the nonempty labels above it; two-year forecast crop labels forward-fill.
            blocks=[]
            for c in years:
                if not blocks or c!=blocks[-1][-1]+1 or years[c]<=years[blocks[-1][-1]]:blocks.append([c])
                else:blocks[-1].append(c)
            above=rows[i-1] if i else []
            next_header=next((j for j in range(i+1,len(rows)) if rows[j] and 'item'==str(rows[j][0] or '').strip().lower()),len(rows))
            section_text=' '.join(str(rr[0] or '') for rr in rows[i+1:next_header] if rr)
            basis='economic_full_ownership' if 'Economic (full ownership)' in section_text else 'cash_costs' if meta['family']=='Historical' else 'forecast_costs'
            if 'forecast' in meta['family']:
                last=''
                for c in years:
                    if c<len(above) and above[c]:last=str(above[c]).strip()
                    if not last:raise FormatError('Missing forecast commodity group')
                    classes[c]=last
            else:
                last_group='not_applicable'
                for block in blocks:
                    labels=[str(above[c]).strip() for c in block if c<len(above) and isinstance(above[c],str) and above[c].strip()]
                    group=' | '.join(labels) or last_group
                    last_group=group
                    for c in block:classes[c]=group
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'year/header row'});continue
        if not years:
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'outside a defined observation block'});continue
        monetary=[v for v in nonempty if re.fullmatch(r'(?i)(?:\(?\s*)?dollars(?:(?:\s+per\s+|\s*/).*)?',v)]
        if monetary and not any(isinstance(row[c],(int,float)) for c in years if c<len(row)):
            unit=monetary[0].strip('() ')
            for block in blocks:
                block_units=[str(row[c]).strip('() ') for c in block if c<len(row) and str(row[c]).strip() in monetary]
                for c in block:units[c]=block_units[0] if block_units else unit
            if unit.lower()=='dollars' and 'per cow' in title.lower():unit='Dollars per cow'
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'unit header'});continue
        if label and (re.match(r'^\d+/|^F\s*=|^Note:|^Source:|^Contact:|^See footnote',label,re.I)):
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'source footnote'});continue
        values=[row[c] if c<len(row) else None for c in years]
        if not any(isinstance(v,(float,int)) or (isinstance(v,str) and re.fullmatch(r'-?\d+(?:\.\d+)?|NA|N/A|\(D\)|--',v.strip())) for v in values):
            if label and label.strip('= -'):
                category=label.rstrip(': ')
            accounting['excluded'].append({'sheet':sheet,'row':i+1,'reason':'blank/section heading'});continue
        if not label or not title or not unit:raise FormatError(f'Incomplete wide-table dimensions: {sheet}, row {i+1}')
        row_unit=unit
        parenthetical=re.search(r'\(([^()]*(?:dollars|bu\.|lbs\.|lb\.|tons|cwt|acre)[^()]*)\)',label,re.I)
        if parenthetical:row_unit=parenthetical.group(1)
        elif label.lower().startswith('pounds of milk per unit'):row_unit='Pounds of milk per cow'
        for c,year in years.items():
            v=row[c] if c<len(row) else None
            if str(v).strip()=='1/' and not (meta['commodity_group']=='Tobacco' and clean_item(text)=='Curing fuel'):
                raise FormatError('Unverified source footnote used as numeric value')
            commodity=classes[c] if 'forecast' in meta['family'] else meta['commodity_group']
            region='U.S. total' if 'forecast' in meta['family'] else re.sub(r'\s+(?:19|20)\d{2}.*$','',sheet).strip()
            cell_unit=units.get(c,row_unit) if row_unit==unit else row_unit
            if cell_unit=='Dollars' and 'per cow' in title.lower():cell_unit='Dollars per cow'
            if cell_unit=='dollars/lb. and cwt.':cell_unit='dollars/cwt.' if 'cwt' in units.get(c,'') else 'dollars/lb.'
            if cell_unit=='lb. and cwt./acre':cell_unit='cwt./acre' if 'cwt' in units.get(c,'') else 'lb./acre'
            data={'methodology':table_title_method(title,basis,sheet), 'Commodity':commodity,'Category':category,'Item':text,'Units':cell_unit,'Region':region,'Year':year,'Value':v,'classification':'not_applicable' if 'forecast' in meta['family'] else classes[c]}
            locator={'sheet':sheet,'row':i+1,'column':c+1}
            if member:locator['member']=member
            accounting['input_data_cells']+=1;numeric_mapped.add((i,c))
            yield observation(data,meta,receipt,locator,member=member,table_title=title,extra={'sheet':sheet,'source_item':text,'source_notes':notes})
    unmapped=all_numeric-numeric_mapped-header_indices
    if unmapped:
        raise FormatError(f'Unaccounted numeric cells: {sheet}: {sorted(unmapped)[:5]}')
    if not numeric_mapped:raise FormatError(f'No mapped wide data: {sheet}')


def workbook_rows(body,kind,meta,receipt,*,member='',accounting):
    if kind=='xls':
        book=xlrd.open_workbook(file_contents=body)
        for sheet in book.sheets():
            rows=[sheet.row_values(i) for i in range(sheet.nrows)]
            yield from wide_rows(rows,meta,receipt,sheet.name,member=member,accounting=accounting)
        book.release_resources()
    else:
        book=openpyxl.load_workbook(io.BytesIO(body),read_only=True,data_only=True)
        try:
            machine=[s for s in book if 'machine readable' in s.title.lower()]
            if len(machine)>1:raise FormatError('Ambiguous machine-readable worksheets')
            if machine:
                sheet=machine[0];rows=sheet.iter_rows(values_only=True);columns=list(next(rows))
                yield from long_rows(rows,columns,meta,receipt,sheet=sheet.title,member=member,accounting=accounting)
                for other in book:
                    if other is not sheet:accounting['excluded'].append({'sheet':other.title,'reason':'presentation of machine-readable observations'})
            else:
                for sheet in book:
                    yield from wide_rows(list(sheet.iter_rows(values_only=True)),meta,receipt,sheet.title,member=member,accounting=accounting)
        finally:book.close()


def parse(path,meta,receipt,*,years=None,accounting=None):
    """Parse one source file; archive members remain distinct forecast vintages."""
    accounting=accounting if accounting is not None else {}
    accounting.update(input_data_cells=0,mapped_rows=0,excluded_year_rows=0,excluded=[],quarantined_rows=0)
    kind=meta['format'];path=Path(path);records=[]
    def source():
        if kind=='csv':
            with path.open(encoding='utf-8-sig',newline='') as stream:
                reader=csv.reader(stream,strict=True);columns=next(reader)
                yield from long_rows(reader,columns,meta,receipt,accounting=accounting)
        elif kind in {'xls','xlsx'}:
            yield from workbook_rows(path.read_bytes(),kind,meta,receipt,accounting=accounting)
        elif kind=='zip':
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if info.is_dir():accounting['excluded'].append({'member':info.filename,'reason':'archive directory'});continue
                    if info.filename.startswith('/') or '..' in Path(info.filename).parts or not info.filename.endswith('.xlsx') or info.file_size>50_000_000:
                        raise FormatError('Unknown/unsafe ERS archive member')
                    yield from workbook_rows(archive.read(info),'xlsx',meta,receipt,member=info.filename,accounting=accounting)
        else:raise FormatError('Unsupported ERS format')
    try:
        for row in source():
            if years is not None and row['year'] not in years:
                accounting['excluded_year_rows']+=1;continue
            records.append(row);accounting['mapped_rows']+=1
        frame=SCHEMA.frame(records)
        if accounting['input_data_cells']!=accounting['mapped_rows']+accounting['excluded_year_rows']:
            raise ValidationError('ERS parser accounting mismatch')
        return frame
    except (ValidationError,FormatError):
        accounting['quarantined_rows']+=1;raise


def validate_years(years):
    if isinstance(years,str):
        try:
            if ':' in years:
                a,b=map(int,years.split(':'));result=list(range(a,b+1))
            else:result=[int(x) for x in years.split(',')]
        except ValueError:raise ConfigurationError('ERS years must be YYYY,YYYY or YYYY:YYYY') from None
    else:
        try:result=list(years)
        except TypeError:raise ConfigurationError('ERS years must be an iterable of observation years') from None
    if not result or any(type(y) is not int or y<1900 or y>2200 for y in result):
        raise ConfigurationError('Invalid ERS observation years')
    return sorted(set(result))


def commodity_matches(meta,commodities):
    if commodities=='all':return True
    selected=commodities.split(',') if isinstance(commodities,str) else list(commodities)
    if not selected:raise ConfigurationError('At least one commodity is required')
    # Forecast files contain multiple crops, so filter their observations after parsing.
    if 'forecast' in meta['family']:return True
    return any(slug(c)==slug(meta['commodity_group']) or (slug(c)=='hogs' and slug(meta['commodity_group']).startswith('hogs')) for c in selected)


def iter_download(years,*,commodities='all',data_dir='data',refresh=False,client=None):
    """Yield complete validated file partitions, then select requested years.

    Every source file is replaced as a whole on revision; historical vintages and
    enterprise/method distinctions survive. At most one workbook/archive is in
    memory. CLI final export selection occurs only after all selected files succeed.
    """
    years=validate_years(years);store=Store(data_dir);owned=client is None;client=client or HTTPClient()
    try:
        discovery_path=store.root/'manifests/costs-returns/discovery.json'
        records=discover(client,store) if refresh or not discovery_path.exists() else json.loads(discovery_path.read_text())
        records=[r for r in records if r['selected'] and commodity_matches(r,commodities)]
        if not records:raise ConfigurationError('No matching ERS product in discovered scope')
        for meta in records:
            cache=store.root/'manifests/costs-returns/urls'/f"{sha256(meta['url'].encode())}.json"
            if cache.exists() and not refresh:
                receipt=json.loads(cache.read_text());path=store.artifact(receipt['source_artifact_id'])
            else:
                body,headers=client.get(meta['url'],expected=meta['format'])
                receipt=store.raw(body,metadata=headers)
                if cache.exists():
                    previous=json.loads(cache.read_text())
                    if previous['source_artifact_id']==receipt['source_artifact_id']:receipt=previous
                atomic_write(cache,canonical(receipt));path=store.artifact(receipt['source_artifact_id'])
            accounting={}
            try:
                frame=parse(path,meta,receipt,accounting=accounting)
                snapshot=store.publish('costs-returns',meta['partition'],frame,SCHEMA,[receipt['source_artifact_id']],parser_version=PARSER_VERSION,configuration={k:meta[k] for k in ['family','commodity_group','source_release_date','format']})
                frame=SCHEMA.read_csv(store.root/snapshot['csv_path'])
                selected=frame[frame['year'].isin(years)]
                if commodities!='all' and 'forecast' in meta['family']:
                    names=commodities.split(',') if isinstance(commodities,str) else list(commodities)
                    selected=selected.loc[selected['commodity'].map(lambda x:slug(x) in {slug(n) for n in names}).astype(bool)]
                yield selected.reset_index(drop=True)
            finally:
                atomic_write(store.root/'manifests/costs-returns/accounting'/f"{receipt['source_artifact_id']}.json",canonical(accounting))
    finally:
        if owned:client.close()
