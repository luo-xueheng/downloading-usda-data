"""Freeze mandatory table families before implementation; narrative charts are classified separately."""
from pathlib import Path
import json,re,pdfplumber
ROOT=Path(__file__).resolve().parents[3];records=[]
for family in ['world-production','grain-trade','oilseed-trade']:
 path=ROOT/f'tests/fixtures/raw/{family}-development.pdf'
 current='';changes=[]
 with pdfplumber.open(path) as pdf:
  for i,page in enumerate(pdf.pages,1):
   text=page.extract_text(x_tolerance=1,y_tolerance=3) or '';lines=text.splitlines();first=lines[0] if lines else ''
   if first in {'WHEAT','RICE','COARSE GRAINS'}:current=first
   numbered=re.match(r'Table\s+(\d{1,2})\b',first,re.I)
   main=numbered or (family=='grain-trade' and (first=='All Grain Summary Comparison' or re.match(r'(World|Regional) .*(Trade|Stocks)$',first)))
   if main:
    title=first if first!='TABLE 18' else 'TABLE 18 Reliability of Production Projections'
    records.append({'family':family,'table_title':title,'required':True,'source_page':i,'status':'unresolved','reason':'All numbered/appendix numerical table families remain mandatory; parser and mappings not accepted yet.'})
   for match in re.finditer(r'(TRADE CHANGES IN [^\n]+|\d{4}/\d{2} OUTLOOK CHANGES[^\n]+)',text):
    title=match.group(0).split(' – ')[0]
    records.append({'family':family,'table_title':(current+' | ' if family=='grain-trade' else '')+title,'required':True,'source_page':i,'status':'unresolved','reason':'Numerical changes table in report body; continuation pages are part of the same table.'})
   if not main and not re.search('TRADE CHANGES IN|OUTLOOK CHANGES',text):
    records.append({'family':family,'table_title':f'Non-table page {i}: {first}','required':False,'source_page':i,'status':'not_applicable','reason':'Narrative, chart/map, administrative schedule or definitions; no narrative-number extraction is promised. Any continuing numerical change table is nevertheless required with its starting table.'})
obj={'selected_before_implementation':True,'required_policy':'All numbered appendix tables, grain appendix supply/trade tables, and every explicit trade/outlook changes table are mandatory. Narrative paragraphs, charts/maps, calendars and contact lists are not structured business tables.','tables':records}
(ROOT/'config/report_table_inventory.json').write_text(json.dumps(obj,indent=2)+'\n')
print('Required tables',sum(r['required'] for r in records))
