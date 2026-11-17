"""FAS ESR weekly data with endpoint-defined marketing years and exact quantities."""
from datetime import date,datetime
from decimal import Decimal
import json
from pathlib import Path
import pandas as pd
from .fas_common import cached_response,selected_codes,marketing_years,client_config
from ..http import HTTPClient
from ..schema import Field,Schema
from ..storage import Store,atomic_write,canonical
from ..errors import FormatError,ValidationError

DICTIONARIES=['commodities','countries','regions','unitsOfMeasure','datareleasedates']
METRICS=['weeklyExports','accumulatedExports','outstandingSales','grossNewSales','currentMYNetSales','currentMYTotalCommitment','nextMYOutstandingSales','nextMYNetSales']
SOURCE_FIELDS={'commodityCode','countryCode','unitId','weekEndingDate',*METRICS}
PARSER_VERSION='fas-esr-1'
SCHEMA=Schema('esr_weekly_sales','1',tuple([
 Field('commodityCode','string',False,'Official ESR commodity code','commodityCode',key=True),Field('countryCode','string',False,'Official destination/aggregate code','countryCode',key=True),Field('marketYear','string',False,'Marketing-year identifier supplied to the endpoint, not inferred from week date','request marketYear',key=True),Field('weekEndingDate','date',False,'Official week ending; boundary weeks may appear in adjacent MY partitions','weekEndingDate',key=True),Field('unitId','string',False,'Official source quantity unit code','unitId',key=True),Field('commodity_name','string',False,'Official commodity/class label','commodities.commodityName'),Field('destination_name','string',False,'Official country/aggregate label','countries.countryDescription'),Field('region_id','string',False,'Official destination-region membership, not an extra aggregate row','countries.regionId'),Field('region_name','string',False,'Region label','regions.regionName'),Field('genc_code','string',True,'Optional official geography code; null stays null','countries.gencCode'),Field('unit','string',False,'Source quantity scale/denomination','unitsOfMeasure.unitNames')]+[
 Field(m,'decimal',True,'Distinct official ESR metric; signed values retained',m,'unit column') for m in METRICS]+[
 Field('raw_metrics','string',False,'Exact lexical numeric or null representations','source JSON'),Field('source_week_raw','string',False,'Original source week-ending timestamp, no timezone invented','weekEndingDate'),Field('commodity_release_timestamp_raw','string',False,'Latest commodity-level API release metadata; not historical report publication time','datareleasedates.releaseTimeStamp'),Field('source_release_date','date',True,'Unknown historical per-partition publication date','not asserted from commodity-level latest release'),Field('source_release_at_utc','datetime',True,'Unknown exact historical publication instant','source does not provide a zoned partition release timestamp'),Field('release_time_precision','string',False,'unknown for historical partition publication','source metadata'),Field('retrieved_at_utc','datetime',False,'UTC response capture','receipt'),Field('source_artifact_id','string',False,'Response bytes SHA256','raw storage'),Field('snapshot_id','string',False,'Parser/schema/config/artifact identity','normalized manifest'),Field('vintage_type','string',False,'Current revised weekly historical series','API source semantics')]))


def validate_dictionaries(dictionaries):
    expected={'commodities':({'commodityCode','commodityName','unitId'},'commodityCode'),'countries':({'countryCode','countryName','countryDescription','regionId','gencCode'},'countryCode'),'regions':({'regionId','regionName'},'regionId'),'unitsOfMeasure':({'unitId','unitNames'},'unitId'),'datareleasedates':({'commodityCode','marketYearStart','marketYearEnd','marketYear','releaseTimeStamp'},'commodityCode')}
    indexed={}
    for name,(fields,key) in expected.items():
        rows=dictionaries[name]
        if not isinstance(rows,list) or not rows or any(set(r)!=fields for r in rows):
            raise FormatError('Unknown/empty ESR dictionary response layout: '+name)
        index={str(r[key]):r for r in rows}
        if len(index)!=len(rows):raise ValidationError('Duplicate ESR dictionary codes')
        indexed[name]=index
    for r in dictionaries['commodities']:
        if str(r['unitId']) not in indexed['unitsOfMeasure']:raise ValidationError('Unknown commodity unit code')
    for r in dictionaries['countries']:
        if str(r['regionId']) not in indexed['regions']:raise ValidationError('Unknown country region')
    return indexed


def discover(client,store,*,refresh=False):
    dictionaries={};artifacts=[]
    for name in DICTIONARIES:
        body,receipt=cached_response(store,'/api/esr/'+name,client=client,refresh=refresh)
        dictionaries[name]=json.loads(body);artifacts.append(receipt['source_artifact_id'])
    validate_dictionaries(dictionaries)
    atomic_write(store.root/'manifests/export-sales/dictionaries.json',canonical({'dictionaries':dictionaries,'artifact_ids':artifacts}))
    return dictionaries,artifacts


def parse(body,dictionaries,receipt,*,commodity,market_year,expected_records=None):
    try:rows=json.loads(body,parse_float=Decimal)
    except (ValueError,UnicodeError):raise FormatError('Truncated or invalid ESR JSON response') from None
    if not isinstance(rows,list):raise FormatError('ESR response is not the documented complete array')
    if expected_records is not None and len(rows)!=expected_records:
        raise ValidationError('ESR response record count differs from independently pinned expected count')
    indexed=validate_dictionaries(dictionaries);commodity=str(commodity);market_year=str(market_year)
    if commodity not in indexed['commodities']:raise ValidationError('Unknown ESR commodity code')
    records=[]
    for row in rows:
        if set(row)!=SOURCE_FIELDS:raise FormatError('Unauthorized ESR response field change')
        code=str(row['commodityCode']);country=str(row['countryCode']);unit=str(row['unitId'])
        if code!=commodity or country not in indexed['countries'] or unit not in indexed['unitsOfMeasure']:
            raise ValidationError('Unknown or mismatched ESR commodity/destination/unit')
        if str(indexed['commodities'][code]['unitId'])!=unit:raise ValidationError('ESR observation unit disagrees with dictionary')
        try:
            week=datetime.fromisoformat(row['weekEndingDate'])
            if week.time()!=datetime.min.time():raise ValueError()
        except (ValueError,TypeError):raise FormatError('Unexpected ESR week-ending value') from None
        values={}
        for metric in METRICS:
            value=row[metric]
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,Decimal))):
                raise FormatError('Unknown ESR numeric type')
            values[metric]=Decimal(value) if value is not None else None
        destination=indexed['countries'][country];region=indexed['regions'][str(destination['regionId'])]
        release=indexed['datareleasedates'].get(commodity,{})
        records.append(dict(commodityCode=code,countryCode=country,marketYear=market_year,weekEndingDate=week.date(),unitId=unit,commodity_name=indexed['commodities'][code]['commodityName'],destination_name=destination['countryDescription'].strip(),region_id=str(destination['regionId']),region_name=region['regionName'],genc_code=destination['gencCode'],unit=indexed['unitsOfMeasure'][unit]['unitNames'],**values,raw_metrics=json.dumps({m:None if row[m] is None else str(row[m]) for m in METRICS},sort_keys=True),source_week_raw=row['weekEndingDate'],commodity_release_timestamp_raw=release.get('releaseTimeStamp','unknown'),source_release_date=None,source_release_at_utc=None,release_time_precision='unknown',retrieved_at_utc=datetime.fromisoformat(receipt['retrieved_at_utc']),source_artifact_id=receipt['source_artifact_id'],snapshot_id='unpublished',vintage_type='current_revised'))
    return SCHEMA.frame(records)


def path_for(commodity,year,country='all'):
    if not str(commodity).isdigit() or not str(year).isdigit() or country!='all' and not str(country).isdigit():
        raise ValidationError('Invalid ESR partition identifier')
    destination='allCountries' if country=='all' else 'countryCode/'+str(country)
    return f'/api/esr/exports/commodityCode/{commodity}/{destination}/marketYear/{year}'


def iter_download(commodities,market_years,*,countries='all',data_dir='data',refresh=False,client=None):
    """Yield complete commodity/year partitions; refresh all explicitly requested years.

    All-country source responses are preserved. Destination filtering happens only
    after complete-partition validation/publication. Earlier snapshots survive.
    """
    years=marketing_years(market_years);store=Store(data_dir);owned=client is None;client=client or HTTPClient(client_config())
    try:
        dictionaries,artifacts=discover(client,store,refresh=refresh)
        aliases={'wheat':next(str(r['commodityCode']) for r in dictionaries['commodities'] if r['commodityName']=='All Wheat')}
        codes=selected_codes(commodities,dictionaries['commodities'],'commodityCode','commodityName',aliases=aliases)
        destinations=selected_codes(countries,dictionaries['countries'],'countryCode','countryDescription')
        for code in codes:
            for year in years:
                body,receipt=cached_response(store,path_for(code,year),client=client,refresh=refresh)
                frame=parse(body,dictionaries,receipt,commodity=code,market_year=year)
                accounting={'input_records':len(json.loads(body)),'normalized_records':len(frame),'quarantined_records':0,'empty_source_response':not len(frame),'source_year':str(year),'source_artifact_id':receipt['source_artifact_id']}
                manifest=store.publish('export-sales',f'{code}-{year}',frame,SCHEMA,[receipt['source_artifact_id'],*artifacts],parser_version=PARSER_VERSION,configuration={'commodityCode':code,'marketYear':str(year),'source_year_semantics':'endpoint identifier, not week-ending calendar year'})
                atomic_write(store.root/'manifests/export-sales/accounting'/f'{code}-{year}-{receipt["source_artifact_id"]}.json',canonical(accounting))
                latest=SCHEMA.read_csv(store.root/manifest['csv_path'])
                yield latest.loc[latest['countryCode'].isin(destinations)].reset_index(drop=True)
    finally:
        if owned:client.close()
