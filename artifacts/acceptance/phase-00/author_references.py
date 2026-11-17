"""Record independently transcribed expectations; never import a source adapter.

Values below were read from raw CSV/XML/ZIP lines and rendered official PDF pages.
This is an acquisition-time record, not a generator of parser-derived expectations.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
CAT=json.loads((ROOT/'tests/fixtures/catalog.json').read_text())
ART={a['artifact_id']:a for a in CAT['artifacts']}
REF=[]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def add(artifact,locator,dimensions,value,unit,readback,method='Independent manual transcription from the identified raw source cell; no application parser exists.'):
 a=ART[artifact]
 REF.append(dict(reference_id=f'P00-REF-{len(REF)+1:03}',artifact_id=artifact,source_url=a['url'],artifact_sha256=a['sha256'],source=a['source'],fixture_role=a['role'],locator=locator,dimensions=dimensions,expected_value=value,expected_unit=unit,vintage=a['vintage'],vintage_precision=a['vintage_precision'],vintage_type=a['vintage_type'],retrieved_at_utc=a['checked_at_utc'],reference_creation_method=method,tolerance='0',readback=readback))

for role,vals in [('development',['2858.10','3653.95','500.19']),('holdout',['2858.26','3653.72','500.21'])]:
 for attr,value in zip(['Output','Total\r\nSupply','Trade 2/'],vals):
  xp="./sr08/Report/matrix1/m1_commodity_group_Collection/m1_commodity_group[@commodity1='Total Grains 4/']/m1_year_group_Collection/m1_year_group[@market_year1='2024/25']/m1_month_group_Collection/m1_month_group[@forecast_month1='']/m1_attribute_group_Collection/m1_attribute_group/s3[@attribute1="+repr(attr)+"]/s4/Cell"
  # ElementTree XPath does not interpret Python escapes. Store actual CR/LF in attributes.
  xp=xp.replace('\\r','\r').replace('\\n','\n')
  add('wasde-'+role,'sr08; matrix1 World; Total Grains 4/; 2024/25; '+attr.replace('\r\n',' '),dict(table='sr08',geography='World',commodity='Total Grains 4/',market_year='2024/25',forecast_month='',indicator=attr),'{}'.format(value),'Million Metric Tons',dict(kind='xml',xpath=xp,attribute='cell_value1',unit_xpath='./sr08/Report',unit_attribute='sub_report_subtitle'))

corn=[('Gross value of production','Primary product, grain','dollars per planted acre','Eastern Uplands','757.13'),('Supporting information','Price','dollars per bushel at harvest','Prairie Gateway','4'),('Operating costs','Interest on operating capital','dollars per planted acre','Southern Seaboard','10.05')]
soy=[('Allocated overhead','Hired labor','dollars per planted acre','Prairie Gateway','13.8'),('Allocated overhead','Taxes and insurance','dollars per planted acre','Prairie Gateway','14.24'),('Operating costs','Purchased irrigation water','dollars per planted acre','Southern Seaboard','0.18')]
for role,commodity,survey,rows in [('development','Corn','Base survey of 2021',corn),('holdout','Soybean','Base survey of 2023',soy)]:
 for rownum,(category,item,unit,region,value) in enumerate(rows,1):
  dims={'Commodity':commodity,'Category':category,'Item':item,'Units':unit,'Size':'No specific size','Region':region,'Country':'United States','Year':'2025','Survey base year':survey}
  add('ers-'+role,f'CSV data record {rownum} (header excluded), Value column',dims,value,unit,dict(kind='csv',row=rownum,column='Value',unit_column='Units',dimension_columns=dims))

for role,year,county,name,member,vals in [('development','2025','240','Southeast Fairbanks','sobcov_2025.txt',['2','200','29930']),('holdout','2010','999','All Other Counties','sobcov10.txt',['1','27','0'])]:
 dims=dict(commodity_year=year,state_code='02',state_abbreviation='AK',county_code=county,county_name=name,commodity_code='9999',commodity_name='All Other Crops',insurance_plan_code='90',insurance_plan_abbreviation='APH',coverage_category='A',delivery_type='RBUP',coverage_level='.5000',quantity_type='Acres')
 fields={'1':year,'2':'02','3':'AK','4':county,'5':name,'6':'9999','7':'All Other Crops','8':'90','9':'APH','10':'A','11':'RBUP','12':'.5000','18':'Acres'}
 for col,indicator,unit,value in zip([13,19,27],['Policies Sold Count','Net Reported Quantity','Indemnity Amount ($)'],['policies','Acres','USD'],vals):
  add('rma-'+role,f'{member}, line 1, pipe field {col}; layout pages 1-3 dated 2026-05-28',dict(dims,indicator=indicator),value,unit,dict(kind='zip_pipe',member=member,line=1,field=col,expected_width=28,dimension_fields=fields,unit_field=18 if col==19 else None,layout_artifact_id='rma-layout'))

page_map={'world-production-development':1,'world-production-holdout':1,'grain-trade-development':18,'grain-trade-holdout':20,'oilseed-trade-development':10,'oilseed-trade-holdout':10}
def pdf_spec(artifact):
 page=page_map[artifact]
 text=(ROOT/f'artifacts/acceptance/phase-00/discovery/{artifact}.txt').read_text().split(f'=== PDF PAGE {page} ===\n')[1].split('=== PDF PAGE ')[0]
 path=f'tests/fixtures/references/pages/{artifact}.txt'
 (ROOT/path).write_text(text)
 png=f'tests/fixtures/references/pages/{artifact}.png'
 return dict(kind='pdf_independent_transcript',page=page,transcript_path=path,transcript_sha256=sha(path),image_path=png,image_sha256=sha(png),transcription_tool='pypdf PdfReader.extract_text(extraction_mode="layout"); visually checked against pdftoppm page render',visual_checked=True)
for role,country,commodity,vals,patterns in [
 ('development','Argentina','Wheat',['23.0','3.59','6.4'],[r'MY\) 2026/27 at ([0-9.]+) million',r'Wheat yield is estimated at ([0-9.]+)',r'Harvested area is estimated at ([0-9.]+) million']),
 ('holdout','Indonesia','Palm oil',['45.0','3.21','14.0'],[r'palm oil production at ([0-9.]+) million',r'Yield is estimated at ([0-9.]+)',r'Harvested area is estimated at ([0-9.]+) million'])]:
 artifact='world-production-'+role
 for indicator,value,unit,pattern in zip(['Production','Yield','Harvested area'],vals,['million metric tons','tons per hectare','million hectares'],patterns):
  add(artifact,'PDF page 1, first commodity paragraph, '+indicator,dict(commodity=commodity,geography=country,market_year='2026/27',indicator=indicator),value,unit,dict(pdf_spec(artifact),regex=pattern),method='Manual visual transcription of the rendered official PDF page, independently cross-checked with generic PDF text extraction; no report adapter used.')
for role,vals,page in [('development',['32500','26500','23000'],18),('holdout',['31000','26000','21500'],20)]:
 artifact='grain-trade-'+role
 for country,value in zip(['Australia','Ukraine','Argentina'],vals):
  add(artifact,f'PDF page {page}; World Wheat Production, Consumption, and Stocks; Production; {country}; last 2026/27 column',dict(commodity='Wheat',geography=country,market_year='2026/27',year_basis='Local Marketing Years',indicator='Production',column_month='Nov' if role=='development' else 'Oct'),value,'Thousand Metric Tons',dict(pdf_spec(artifact),section_start='Production',section_end='Total Consumption',row_label=country,column_token=-1,unit_text='Local Marketing Years, Thousand Metric Tons'),method='Manual visual transcription of the rendered PDF table with explicit final-column alignment; generic text readback only.')
for role,vals in [('development',['442.50','100.25','39.54']),('holdout',['442.70','99.57','39.77'])]:
 artifact='oilseed-trade-'+role
 for commodity,value in zip(['Soybean','Rapeseed','Cottonseed'],vals):
  add(artifact,f'PDF page 10; Table 01 Major Oilseeds; Production; Oilseed, {commodity}; last 2026/27 column',dict(commodity='Oilseed, '+commodity,geography='World',market_year='2026/27',indicator='Production',column_month='Nov' if role=='development' else 'Oct'),value,'Million Metric Tons',dict(pdf_spec(artifact),section_start='Production',section_end='Imports',row_label='Oilseed, '+commodity,column_token=-1,unit_text='Million Metric Tons'),method='Manual visual transcription of the rendered PDF table; final column checked visually because earlier columns merge in generic PDF text extraction.')
for row,indicator,value in [(1,'Beginning Stocks','1123.00'),(2,'Domestic','4207.00')]:
 dims={'WasdeNumber':'677','ReportDate':'November 2026','ReportTitle':'Mexico Sugar Supply and Use and High Fructose Corn Syrup Consumption','Attribute':indicator,'ReliabilityProjection':'','Commodity':'Sugar','Region':'Mexico','MarketYear':'2025/26','ProjEstFlag':'Est.','AnnualQuarterFlag':'Annual','Unit':'1000 Metric Tons, Actual Weight','ReleaseDate':'2026-11-10','ReleaseTime':'12:00:00.0000000','ForecastYear':'2026','ForecastMonth':'11'}
 add('wasde-supplemental',f'CSV data record {row}, Value column',dims,value,'1000 Metric Tons, Actual Weight',dict(kind='csv',row=row,column='Value',unit_column='Unit',dimension_columns=dims))
(ROOT/'tests/fixtures/references/observations.json').write_text(json.dumps({'schema_version':1,'creation_date':'2026-11-12','author':'Codex; manual independent source reading','tolerance_policy':'Exact Decimal equality at source precision; zero tolerance selected before verification. No API/report cross-vintage numerical comparisons in Phase 00.','observations':REF},indent=2)+'\n')
print('Independently authored references:',len(REF))
