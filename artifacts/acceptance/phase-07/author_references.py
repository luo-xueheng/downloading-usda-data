"""Independent raw pipe-field references, quantities and disjoint subtotals."""
from pathlib import Path
from decimal import Decimal
import csv,io,json,zipfile,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];refs=[];inventories=[];totals=[]
metrics={12:'policies_sold',13:'policies_earning_premium',16:'units_indemnified',18:'net_reported_quantity',20:'liability_amount',21:'total_premium',22:'subsidy_amount',26:'indemnity_amount',27:'loss_ratio'}
for role,name in [('development','rma-development'),('holdout','rma-holdout')]:
 p=ROOT/f'tests/fixtures/raw/{name}.zip';a=json.loads(Path(str(p)+'.acquisition.json').read_text());sha=hashlib.sha256(p.read_bytes()).hexdigest()
 chosen=[];seen=set();quantities=collections.Counter();categories=set();state_codes=set();counts=0;negative=None;nonacre=None;partition_sums={}
 with zipfile.ZipFile(p) as z:
  member=z.namelist()[0]
  for line,row in enumerate(csv.reader(io.TextIOWrapper(z.open(member),encoding='utf-8-sig'),delimiter='|'),1):
   assert len(row)==28
   r=[x.strip() for x in row];counts+=1;quantities[r[17]]+=1;categories.add((r[7],r[9],r[10],r[11]));state_codes.add(r[1])
   sample=(r[1],r[7],r[9])
   if r[1] in {'02','04','06'} and sample not in seen and len(chosen)<6:
    seen.add(sample);chosen.append((line,r))
   if r[1] in {'02','04'} and r[3] not in {'000','999'} and r[17]=='Acres':
    key=(r[0],r[1],r[17]);entry=partition_sums.setdefault(key,{'rows':0,'net_reported_quantity':0,'liability_amount':0,'total_premium':0,'indemnity_amount':0})
    if any(not r[i] for i in [18,20,21,26]):
     entry['excluded_missing_rows']=entry.get('excluded_missing_rows',0)+1;continue
    entry['rows']+=1
    for i,k in [(18,'net_reported_quantity'),(20,'liability_amount'),(21,'total_premium'),(26,'indemnity_amount')]:entry[k]+=int(r[i])
   if r[17] not in {'Acres','Not Reported'} and nonacre is None:nonacre=(line,r)
   if int(r[26])<0 and negative is None:negative=(line,r)
 if negative:chosen.append(negative)
 if nonacre:chosen.append(nonacre)
 for line,r in chosen:
  for index,field in metrics.items():
   refs.append({'reference_id':f'{name}:{line}:{index+1}','role':role,'artifact':str(p.relative_to(ROOT)),'sha256':sha,'source_url':a['url'],'member':member,'locator':{'line':line,'field_1_based':index+1},'grouping_fields':r[:12]+[r[17]],'field':field,'expected_value':r[index],'unit':r[17] if index==18 else 'USD' if index in {20,21,22,26} else 'ratio' if index==27 else 'count','method':'Independent stdlib pipe reader and integer/Decimal field interpretation from official 28-field layout; no production parser'})
 for key,total in partition_sums.items():totals.append({'commodity_year':key[0],'state_code':key[1],'quantity_type':key[2],'county_exclusions':['000','999'],'missing_policy':'Rows with any missing component in the selected subtotal metrics are explicitly excluded and counted','artifact_sha256':sha,**total,'method':'Independent integer sum over disjoint leaf-county source row sets; no state/county aggregate mixing; units never added across quantity types'})
 inventories.append({'role':role,'artifact':str(p.relative_to(ROOT)),'sha256':sha,'member':member,'rows':counts,'quantity_types':dict(quantities),'grouping_categories':len(categories),'state_codes':sorted(state_codes),'negative_indemnity_example':negative[0] if negative else None,'selected_before_adapter':True})
out=ROOT/'tests/fixtures/phase_07';(out/'references.json').write_text(json.dumps(refs,indent=2)+'\n');(out/'inventory.json').write_text(json.dumps(inventories,indent=2)+'\n');(out/'subtotals.json').write_text(json.dumps(totals,indent=2)+'\n')
print('Independent references',len(refs));print(inventories);print('Subtotals',len(totals))
