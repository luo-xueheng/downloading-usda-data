"""Freeze independent ERS reference cells before production adapter work.
Only direct csv/xlrd/openpyxl reading is used. No usda_data imports.
"""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,json,io,zipfile,xlrd,openpyxl
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'tests/fixtures/phase_03'
refs=[]
for name in ['4962-corn.csv','4984-hogs-all.csv','4986-hogs-farrow-finish.csv','4988-hogs-farrow-feeder.csv','4992-hogs-farrow-weanling.csv','4923-cost-of-production-forecasts-for-major-us-field-crops-2026f-2027f.csv']:
 p=OUT/name;a=json.loads(Path(str(p)+'.acquisition.json').read_text());rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
 for i in [0,1,2,3,4,5]:
  r=rows[i];refs.append({'id':f'{name}:{i+2}','artifact':str(p.relative_to(ROOT)),'sha256':a['sha256'],'url':a['url'],'locator':{'record':i+2},'dimensions':{k:v for k,v in r.items() if k!='Value'},'expected_raw':r['Value'],'expected_unit':r['Units'],'method':'Direct stdlib CSV cell reading before adapter implementation; no production imports','role':'development'})
for name,cells in [('4927-us-1975-95.xls',[(8,2,'Dollars per planted acre'),(9,2,'Dollars per planted acre'),(13,2,'Dollars per planted acre'),(58,4,'Dollars per planted acre'),(32,2,'dollars/bu.'),(33,2,'bu./planted acre')]),('4944-us-1980-92-1993-99.xls',[(7,2,'Dollars per cwt'),(15,2,'Dollars per cwt'),(106,2,'Dollars per cow')]),('4928-southeast-1975-95.xls',[(8,2,'Dollars per planted acre'),(9,2,'Dollars per planted acre'),(32,2,'dollars/bu.'),(33,2,'bu./planted acre'),(58,4,'Dollars per planted acre')])]:
 p=OUT/name;a=json.loads(Path(str(p)+'.acquisition.json').read_text());s=xlrd.open_workbook(p).sheet_by_index(0)
 for r,c,u in cells:
  v=s.cell_value(r-1,c-1);refs.append({'id':f'{name}:{s.name}:{r}:{c}','artifact':str(p.relative_to(ROOT)),'sha256':a['sha256'],'url':a['url'],'locator':{'sheet':s.name,'row':r,'column':c},'source_item':s.cell_value(r-1,0),'expected_raw':str(v),'expected_unit':u,'method':'Independent direct BIFF cell reading and title/unit/header inspection before parser implementation','role':'holdout' if name.startswith('4928') else 'development'})
p=OUT/'4924-previously-released-cost-of-production-forecasts.zip';a=json.loads(Path(str(p)+'.acquisition.json').read_text())
with zipfile.ZipFile(p) as z:
 member='Historical Forecast Zip Folder/cop_forecast_June 2020.xlsx';b=openpyxl.load_workbook(io.BytesIO(z.read(member)),read_only=True,data_only=True);s=b['Forecasts']
 for r,c in [(8,2),(9,3),(16,4),(27,5)]:
  refs.append({'id':f'archive-2020:{r}:{c}','artifact':str(p.relative_to(ROOT)),'sha256':a['sha256'],'url':a['url'],'locator':{'member':member,'sheet':'Forecasts','row':r,'column':c},'source_item':s.cell(r,1).value.strip(),'expected_raw':str(s.cell(r,c).value),'expected_unit':'Dollars per planted acre','year_label':s.cell(4,c).value,'method':'Independent openpyxl cell read of a fixed wide forecast table before parser implementation','role':'development'})
 b.close()
(OUT/'references.json').write_text(json.dumps(refs,indent=2)+'\n')
(OUT/'holdouts.json').write_text(json.dumps({'selected_before_adapter':True,'artifacts':['tests/fixtures/phase_03/4928-southeast-1975-95.xls','tests/fixtures/raw/ers-holdout.csv'],'first_adapter_run':'not_run'},indent=2)+'\n')
print('Frozen references',len(refs))
