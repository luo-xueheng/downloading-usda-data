"""Three complete report-family views: current PSD and original report tables."""
from datetime import datetime
import json
import pandas as pd
from . import fas_psd as psd
from .report_tables import SCHEMA as REPORT_SCHEMA
from .reports import iter_structured_reports,FAMILIES
from ..schema import Field,Schema
from ..errors import ConfigurationError,ValidationError

CODE_FIELDS=['commodity_code','geography_code','attribute_code','unit_code','observation_kind']
SCHEMA=Schema('fas_dataset_observations','1',tuple(list(REPORT_SCHEMA.fields)+[Field(n,'string',False,n.replace('_',' '),'original PSD code or not_applicable for report-only source classifications',key=True) for n in CODE_FIELDS]+[Field('source_calendar_year','string',False,'Original PSD update year, not report date','calendarYear or not_applicable'),Field('source_month','string',False,'Original PSD update month','month or not_applicable'),Field('aggregation_level','string',False,'Source geographic aggregation class','PSD metadata or report_defined'),Field('source_region_code','string',False,'Source PSD region membership','regionCode or not_applicable')]))


def from_psd(frame,family):
    mapping=psd.SCOPE['families'][family];codes={c['commodityCode'] for c in mapping['commodities']};attributes={str(a['attributeId']) for a in mapping['attributes']}
    selected=frame[(frame['commodityCode'].isin(codes))&(frame['attributeId'].isin(attributes))]
    rows=[]
    for r in selected.to_dict('records'):
        rows.append(dict(report_family=family,report_period='not_applicable',table_title='PSD current-revised observations',section_label=r['attribute_name'],section_product_type='not_applicable',row_label=r['geography_name'],column_commodity=r['commodity_name'],indicator=r['attribute_name'],period_label=r['marketYear'],comparison_label='not_applicable',unit=r['unit'],value=r['value'],raw_value=r['raw_value'],value_status='missing' if r['value'] is None else 'reported',period_basis='PSD source marketing-year identifier; TY measures retain their source attribute names',table_metadata_id='PSD dictionary snapshot '+r['snapshot_id'],source_page=0,source_occurrences=1,source_locations=json.dumps({'countryCode':r['countryCode'],'attributeId':r['attributeId']}),source_release_date=r['source_release_date'],source_release_at_utc=r['source_release_at_utc'],release_time_precision=r['release_time_precision'],retrieved_at_utc=r['retrieved_at_utc'],source_artifact_id=r['source_artifact_id'],snapshot_id=r['snapshot_id'],vintage_type=r['vintage_type'],commodity_code=r['commodityCode'],geography_code=r['countryCode'],attribute_code=r['attributeId'],unit_code=r['unitId'],observation_kind='psd_current',source_calendar_year=r['calendarYear'],source_month=r['month'],aggregation_level=r['aggregation_level'],source_region_code=r['region_code']))
    return SCHEMA.frame(rows)


def from_report(frame):
    result=frame.copy()
    for name in CODE_FIELDS:result[name]='report_table' if name=='observation_kind' else 'not_applicable'
    result['source_calendar_year']='not_applicable';result['source_month']='not_applicable';result['aggregation_level']='report_defined';result['source_region_code']='not_applicable'
    return SCHEMA.validate(result)


def iter_dataset(family,*,market_years,report_start,report_end,commodities='all',countries='all',data_dir='data',refresh=False):
    """Yield current PSD plus all verified tables in the independently requested report range.

    Report observations retain report vintages. A commodity/country development
    filter selects PSD observations only; requested report tables remain complete
    and carry their own explicit dimensions. Reports are archived as a parsing side
    effect, even if an attachment-display flag is absent. No old report uses today's
    PSD values as a replacement for original source cells.
    """
    if family not in FAMILIES:raise ConfigurationError('Unknown report dataset')
    if not report_start or not report_end:raise ConfigurationError('Complete report datasets require report_start and report_end separately from market_years')
    for frame in psd.iter_download(commodities,market_years,countries=countries,data_dir=data_dir,refresh=refresh,families=[family]):
        yield from_psd(frame,family)
    for frame in iter_structured_reports(family,report_start,report_end,data_dir=data_dir,refresh=refresh):
        yield from_report(frame)


def compare_aligned(report_row,api_row,*,api_report_period,scale=1,tolerance=0):
    """Compare only an explicitly evidenced matching vintage and exact dimensions.

    api_report_period must be independently established by the caller; the PSD
    response update month alone cannot assert a report's exact publication vintage.
    """
    if report_row['report_period']!=api_report_period:return {'status':'vintage_difference','reason':'Different independently identified report/API vintages; no same-vintage numeric equality is claimed'}
    for key in ['commodity_code','geography_code','attribute_code','period_label']:
        if report_row[key]!=api_row[key]:raise ValidationError('Same-vintage comparison dimension mismatch')
    if report_row['unit']!=api_row['unit']:raise ValidationError('Unit mismatch requires an explicit normalized comparison before calling this function')
    from decimal import Decimal
    if abs(report_row['value']-api_row['value']*Decimal(str(scale)))>Decimal(str(tolerance)):
        raise ValidationError('Same-vintage report/API numerical discrepancy')
    return {'status':'pass'}
