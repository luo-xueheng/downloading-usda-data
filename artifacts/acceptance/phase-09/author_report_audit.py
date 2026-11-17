"""Independent fixed-stratum PDF audit transcription, without production parser imports."""
from pathlib import Path
import json,re,hashlib,pdfplumber
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'tests/fixtures/phase_09'
refs=[]
for family in ['world-production','grain-trade','oilseed-trade']:
 for era,period,path in [('early','2010-04',OUT/(family+'-2010-04.pdf')),('middle','2018-06',OUT/(family+'-2018-06.pdf')),('recent','2026-11',ROOT/f'tests/fixtures/raw/{family}-development.pdf')]:
  with pdfplumber.open(path) as pdf:
   title_fragment={'world-production':'Table 04 Corn Area','grain-trade':'World Corn Production, Consumption, and Stocks','oilseed-trade':'Table 11: Palm Oil:'}[family]
   candidates=[(i,p,p.extract_text(x_tolerance=1,y_tolerance=3) or '') for i,p in enumerate(pdf.pages) if title_fragment in (p.extract_text(x_tolerance=1,y_tolerance=3) or '')[:200]]
   assert len(candidates)==1
   index,page,text=candidates[0];lines=text.splitlines();title=lines[0];chosen=[]
   if family=='world-production':
    for geography in ['World','United States','Brazil','Argentina']:
     line=next(l for l in lines if l.startswith(geography+' ') and len(l.split())>=17)
     values=line.split()[-16:]
     for field,position,unit in [('Area',3,'Million hectares'),('Production',11,'Million metric tons')]:chosen.append((geography,field,values[position],unit))
   else:
    target_metrics=['Production','Total Consumption'] if family=='grain-trade' else ['Production','Ending Stocks']
    for metric in target_metrics:
     start=next(i for i,l in enumerate(lines) if l.strip().removesuffix(' none')==metric)
     # Fixed first three numeric source rows and the source world/total row; source
     # dimensions are frozen as printed. This includes smaller producers, not only defaults.
     rows=[]
     for l in lines[start+1:]:
      toks=l.split()
      if len(toks)>6 and all(re.fullmatch(r'-?[\d,]+(?:\.\d+)?|nr',v) for v in toks[-6:]):rows.append((' '.join(toks[:-6]),toks[-1]))
      elif rows:break
     selected=rows[:3]+[next(x for x in reversed(rows) if x[0] in ['World Total','World','Total'])]
     for geography,value in selected:chosen.append((geography,metric,value,'Thousand Metric Tons'))
   assert len(chosen)==8
   image=ROOT/f'artifacts/acceptance/phase-09/{family}-{era}-audit.png';page.to_image(resolution=140).save(image)
   print(family,period,'page',index+1,chosen)
   for i,(geography,metric,value,unit) in enumerate(chosen):refs.append({'reference_id':f'{family}-{era}-{i}','dataset':family,'artifact':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_report_period':period,'source_page':index+1,'table_title':title,'row_label':geography,'indicator':metric,'comparison_label':{'2010-04':'Apr','2018-06':'Jun','2026-11':'Nov'}[period],'expected_value':value.replace(',',''),'expected_unit':unit,'method':'Independent fixed-row direct PDF text reading plus rendered audit page, no production parser; frozen before audit comparison','stratum':era})
(OUT/'report_audit_references.json').write_text(json.dumps(refs,indent=2)+'\n')
