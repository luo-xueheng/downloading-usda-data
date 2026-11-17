"""Shared report-scoped PSD observations, without fabricated historical vintages."""
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import re
import pandas as pd
from .fas_common import cached_response,selected_codes,marketing_years,client_config
from ..http import HTTPClient
from ..schema import Field,Schema
from ..storage import Store,atomic_write,canonical
from ..errors import ConfigurationError,FormatError,ValidationError

SCOPE=json.loads(Path(__file__).with_name('psd_scope.json').read_text())
DICTIONARIES=['commodities','countries','regions','unitsOfMeasure','commodityAttributes']
FIELDS={'commodityCode','countryCode','marketYear','calendarYear','month','attributeId','unitId','value'}
PARSER_VERSION='fas-psd-1'
REGIONAL_CODES={'BE','C1','E2','E3','E4'}
RESIDUAL_CODES={'T3','X8','ZZ','Z7'}
SCHEMA=Schema('psd_observations','1',tuple([
 Field('commodityCode','string',False,'Original seven-digit commodity code, leading zeros retained','commodityCode',key=True),Field('countryCode','string',False,'Original country/aggregate code; 00 denotes source world endpoint','countryCode',key=True),Field('aggregation_level','string',False,'country, region, residual_aggregate or world','verified endpoint and country dictionary',key=True),Field('marketYear','string',False,'Source marketing-year identifier, not converted to calendar year','marketYear',key=True),Field('attributeId','string',False,'Official attribute code','attributeId',key=True),Field('unitId','string',False,'Official original unit/scale code','unitId',key=True),Field('calendarYear','string',False,'Source record update year; not original report vintage','calendarYear'),Field('month','string',False,'Source update month, retaining leading zero','month'),Field('commodity_name','string',False,'Official commodity description','commodities.commodityName'),Field('geography_name','string',False,'Official geography description','countries.countryName or world endpoint'),Field('region_code','string',False,'Membership metadata; not an additional total','countries.regionCode or R00'),Field('region_name','string',True,'Official region name; null when source countries refer to an absent region dictionary row','regions.regionName'),Field('region_mapping_status','string',False,'resolved or absent_in_source_dictionary; original region code is always retained','dictionary cross-reference'),Field('genc_code','string',True,'Optional source geography code','countries.gencCode'),Field('attribute_name','string',False,'Official attribute label','commodityAttributes.attributeName'),Field('unit','string',False,'Source unit description with surrounding whitespace trimmed only','unitsOfMeasure.unitDescription'),Field('unit_raw','string',False,'Original unit descriptor including lexical padding','unitsOfMeasure.unitDescription'),Field('value','decimal',True,'Exact numeric value in original source unit; missing not zero','value','unit column'),Field('raw_value','string',False,'Original numeric or null representation','value'),Field('source_release_period','string',False,'Source year-month update label, not invented exact date','calendarYear and month'),Field('source_release_date','date',True,'Exact publication day unavailable','source does not provide day'),Field('source_release_at_utc','datetime',True,'Exact publication instant unavailable','source does not provide time'),Field('release_time_precision','string',False,'month; no day or clock inferred','source year-month metadata'),Field('retrieved_at_utc','datetime',False,'UTC capture timestamp','receipt'),Field('source_artifact_id','string',False,'Exact response hash','raw archive'),Field('snapshot_id','string',False,'Version-aware snapshot identity','normalized manifest'),Field('vintage_type','string',False,'current_revised; never historic report vintage','PSD API semantics')]))


def validate_dictionaries(d):
    definitions={'commodities':({'commodityCode','commodityName'},'commodityCode'),'countries':({'countryCode','countryName','regionCode','gencCode'},'countryCode'),'regions':({'regionCode','regionName'},'regionCode'),'unitsOfMeasure':({'unitId','unitDescription'},'unitId'),'commodityAttributes':({'attributeId','attributeName'},'attributeId')}
    indexed={}
    for name,(fields,key) in definitions.items():
        rows=d[name]
        if not isinstance(rows,list) or not rows or any(set(r)!=fields for r in rows):raise FormatError('Unknown PSD dictionary layout: '+name)
        indexed[name]={str(r[key]):r for r in rows}
        if len(indexed[name])!=len(rows):raise ValidationError('Duplicate PSD dictionary code')
    if not set(SCOPE['commodity_union'])<=set(indexed['commodities']):raise ValidationError('Frozen report commodities missing from API dictionary')
    return indexed


def discover(client,store,*,refresh=False):
    d={};artifacts=[]
    for name in DICTIONARIES:
        body,receipt=cached_response(store,'/api/psd/'+name,client=client,refresh=refresh)
        d[name]=json.loads(body);artifacts.append(receipt['source_artifact_id'])
    validate_dictionaries(d)
    atomic_write(store.root/'manifests/psd/dictionaries.json',canonical({'dictionaries':d,'artifact_ids':artifacts,'scope':SCOPE}))
    return d,artifacts


def path_for(commodity,year,geography='all'):
    if not re.fullmatch(r'\d{7}',str(commodity)) or not str(year).isdigit():raise ConfigurationError('Invalid PSD code/year')
    if geography=='world':return f'/api/psd/commodity/{commodity}/world/year/{year}'
    if geography!='all' and not re.fullmatch('[A-Z0-9]{2}',geography):raise ConfigurationError('Invalid PSD geography code')
    return f'/api/psd/commodity/{commodity}/country/{geography}/year/{year}'


def release_inventory(body,commodity):
    rows=json.loads(body);fields={'commodityCode','countryCode','marketYear','releaseYear','releaseMonth'}
    if not isinstance(rows,list) or any(set(r)!=fields or r['commodityCode']!=commodity for r in rows):raise FormatError('Unknown PSD release inventory layout')
    keys=[(r['countryCode'],r['marketYear']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValidationError('Duplicate PSD release inventory key')
    return rows


def parse(body,dictionaries,receipt,*,commodity,market_year,geography='all',expected_records=None,accounting=None):
    indexed=validate_dictionaries(dictionaries)
    if commodity not in SCOPE['commodity_union']:raise ConfigurationError('PSD commodity outside the three frozen report families')
    try:rows=json.loads(body,parse_float=Decimal)
    except (ValueError,UnicodeError):raise FormatError('Invalid/truncated PSD JSON') from None
    if not isinstance(rows,list):raise FormatError('PSD observation response must be complete array')
    if expected_records is not None and len(rows)!=expected_records:raise ValidationError('PSD source record count mismatch')
    allowed=set(SCOPE['attribute_union_by_commodity'][commodity]);records=[]
    accounting=accounting if accounting is not None else {};accounting.update(input_records=len(rows),mapped_records=0,excluded_attributes={})
    for row in rows:
        if set(row)!=FIELDS:raise FormatError('Unauthorized PSD observation layout change')
        if row['commodityCode']!=commodity or row['marketYear']!=str(market_year):raise ValidationError('PSD response partition does not match request')
        code=row['countryCode'];attr=str(row['attributeId']);unit=str(row['unitId'])
        if attr not in indexed['commodityAttributes'] or unit not in indexed['unitsOfMeasure']:raise ValidationError('Unknown PSD attribute/unit')
        if geography=='world':
            if code!='00':raise ValidationError('World endpoint returned non-world geography')
            name='World';region='R00';genc=None;level='world'
        else:
            if code not in indexed['countries'] or geography!='all' and code!=geography:raise ValidationError('Unknown or mismatched PSD country code')
            country=indexed['countries'][code];name=country['countryName'];region=country['regionCode'];genc=country['gencCode']
            level='region' if code in REGIONAL_CODES else 'residual_aggregate' if code in RESIDUAL_CODES else 'country'
        try:
            datetime(int(row['calendarYear']),int(row['month']),1)
            if not re.fullmatch(r'\d{2}',row['month']):raise ValueError()
        except (ValueError,TypeError):raise FormatError('Invalid PSD source update year-month') from None
        value=row['value']
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,Decimal))):raise FormatError('Unknown PSD numeric type')
        if row['attributeId'] not in allowed:
            accounting['excluded_attributes'][attr]=accounting['excluded_attributes'].get(attr,0)+1;continue
        raw_unit=indexed['unitsOfMeasure'][unit]['unitDescription']
        records.append(dict(commodityCode=commodity,countryCode=code,aggregation_level=level,marketYear=str(market_year),attributeId=attr,unitId=unit,calendarYear=row['calendarYear'],month=row['month'],commodity_name=indexed['commodities'][commodity]['commodityName'],geography_name=name,region_code=region,region_name=indexed['regions'].get(region,{}).get('regionName'),region_mapping_status='resolved' if region in indexed['regions'] else 'absent_in_source_dictionary',genc_code=genc,attribute_name=indexed['commodityAttributes'][attr]['attributeName'],unit=raw_unit.strip(),unit_raw=raw_unit,value=Decimal(value) if value is not None else None,raw_value='null' if value is None else str(value),source_release_period=row['calendarYear']+'-'+row['month'],source_release_date=None,source_release_at_utc=None,release_time_precision='month',retrieved_at_utc=datetime.fromisoformat(receipt['retrieved_at_utc']),source_artifact_id=receipt['source_artifact_id'],snapshot_id='unpublished',vintage_type='current_revised'))
    accounting['mapped_records']=len(records)
    if accounting['input_records']!=accounting['mapped_records']+sum(accounting['excluded_attributes'].values()):raise ValidationError('PSD parser accounting mismatch')
    return SCHEMA.frame(records)


def family_codes(families):
    if not families or set(families)-set(SCOPE['families']):raise ConfigurationError('Unknown report family')
    return sorted({c['commodityCode'] for f in families for c in SCOPE['families'][f]['commodities']})


def iter_download(commodities,market_years,*,countries='all',data_dir='data',refresh=False,client=None,families=None):
    """Fetch each scoped commodity/year once, including its independent world endpoint.

    Country/region/world rows remain distinct. A shared family union avoids repeated
    HTTP requests across reports within one refresh operation. Raw and revised
    snapshots retain exact source field/unit/version provenance.
    """
    years=marketing_years(market_years);store=Store(data_dir);owned=client is None;client=client or HTTPClient(client_config())
    try:
        dictionaries,dict_artifacts=discover(client,store,refresh=refresh)
        in_scope=family_codes(families) if families else SCOPE['commodity_union']
        commodity_dict=[r for r in dictionaries['commodities'] if r['commodityCode'] in in_scope]
        alias={'soybeans':'2222000'}
        codes=selected_codes(commodities,commodity_dict,'commodityCode','commodityName',aliases=alias)
        destinations=selected_codes(countries,[*dictionaries['countries'],{'countryCode':'00','countryName':'World'}],'countryCode','countryName')
        for code in codes:
            release_body,release_receipt=cached_response(store,f'/api/psd/commodity/{code}/dataReleaseDates',client=client,refresh=refresh)
            release_rows=release_inventory(release_body,code)
            atomic_write(store.root/'manifests/psd/periods'/f'{code}.json',canonical({'source_artifact_id':release_receipt['source_artifact_id'],'periods':release_rows}))
            for year in years:
                frames=[];artifacts=[*dict_artifacts,release_receipt['source_artifact_id']];counts={}
                for kind in ['all','world']:
                    body,receipt=cached_response(store,path_for(code,year,kind),client=client,refresh=refresh)
                    acc={};frames.append(parse(body,dictionaries,receipt,commodity=code,market_year=year,geography=kind,accounting=acc));artifacts.append(receipt['source_artifact_id']);counts[kind]=acc
                frame=SCHEMA.validate(pd.concat(frames,ignore_index=True))
                manifest=store.publish('psd',f'{code}-{year}',frame,SCHEMA,artifacts,parser_version=PARSER_VERSION,configuration={'commodityCode':code,'marketYear':str(year),'scope':SCOPE['attribute_union_by_commodity'][code]})
                atomic_write(store.root/'manifests/psd/accounting'/f'{code}-{year}-{manifest["snapshot_id"]}.json',canonical(counts))
                latest=SCHEMA.read_csv(store.root/manifest['csv_path'])
                yield latest.loc[latest['countryCode'].isin(destinations)].reset_index(drop=True)
    finally:
        if owned:client.close()
