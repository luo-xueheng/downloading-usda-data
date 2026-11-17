"""Pin exact source year-header defects against a later independently reviewed report."""
from pathlib import Path
import json,pdfplumber,hashlib
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'data'
correct=json.loads((ROOT/'artifacts/acceptance/phase-09/report_partitions/oilseed-trade-2023-09.json').read_text());id=correct['source_artifact_id'];p=DATA/'raw'/id[:2]/id
with pdfplumber.open(p) as pdf:
 text=next(page.extract_text(x_tolerance=1,y_tolerance=3) for page in pdf.pages if (page.extract_text(x_tolerance=1,y_tolerance=3) or '').startswith('Table 31'))
 lines=text.splitlines();start=lines.index('2022/23');signature=next(l for l in lines[start+1:] if l.startswith('Oct '))
 assert signature.startswith('Oct 1,602 1,279 1,292')
repairs={}
for source in (ROOT/'artifacts/acceptance/phase-09/report_partitions').glob('oilseed-trade-2023-*.json'):
 record=json.loads(source.read_text());id=record.get('source_artifact_id')
 if not id:continue
 with pdfplumber.open(DATA/'raw'/id[:2]/id) as pdf:
  for page in pdf.pages:
   t=page.extract_text(x_tolerance=1,y_tolerance=3) or ''
   if not t.startswith('Table 31'):continue
   lines=t.splitlines()
   if lines.count('2021/22')==2:
    second=[i for i,l in enumerate(lines) if l=='2021/22'][1]
    first_values=next(l for l in lines[second+1:] if l.startswith('Oct '))
    assert first_values==signature
    repairs[id]={'id':'OIL-PRICE-2022-23-MISLABEL','table_title':'Table 31: Vegetable Oil Prices','original_year':'2021/22','occurrence':2,'normalized_year':'2022/23','matching_first_row':signature,'evidence_source_artifact_id':correct['source_artifact_id'],'evidence_url':correct['url'],'evidence_locator':'Table 31 in September 2023 report, explicit 2022/23 header and identical 13 October quote values; visually reviewed original page','rule':'Only the exact defective artifact, repeated source header and exact full first-row match qualify; numeric values are never edited.'}
(ROOT/'src/usda_data/sources/report_dimension_repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
(ROOT/'artifacts/acceptance/phase-09/report_dimension_repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
print('Exact report year-header repairs',len(repairs))
