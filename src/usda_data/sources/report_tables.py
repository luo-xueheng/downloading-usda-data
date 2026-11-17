"""Focused numerical tables in the three FAS circulars; source labels are keys.

Narrative prose/chart-axis numbers are not observations. Unsupported tables and
ambiguous layouts fail instead of returning apparently complete partial data.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import io,json,re
import pdfplumber
from ..schema import Field,Schema
from ..errors import FormatError,ValidationError
from ..storage import canonical,sha256

KEYS=['report_family','report_period','table_title','section_label','section_product_type','row_label','column_commodity','indicator','period_label','comparison_label','unit']
SCHEMA=Schema('fas_report_observations','1',tuple([Field(k,'string',False,k.replace('_',' '),'original report table labels / documented whitespace normalization',key=True) for k in KEYS]+[
 Field('value','decimal',True,'Exact displayed report value','numeric cell','unit column'),Field('raw_value','string',False,'Original displayed number or missing marker','numeric cell'),Field('value_status','string',False,'reported, not_reported or not_applicable','source marker'),Field('period_basis','string',False,'Original table period definition, including MY versus TY','table caption and notes'),Field('table_metadata_id','string',False,'Hash of complete header/notes/mapping metadata; does not replace business dimensions','table metadata archive'),Field('source_page','integer',False,'First source page of this observation','PDF page'),Field('source_occurrences','integer',False,'Number of explicitly investigated identical repeated source cells','source duplicate accounting'),Field('source_locations','string',False,'All physical source locators and lexical values for repeated cells','PDF table positions'),Field('source_release_date','date',True,'Official exact publication date when independently verified; otherwise null','report discovery metadata'),Field('source_release_at_utc','datetime',True,'No exact publication clock inferred','source metadata'),Field('release_time_precision','string',False,'day when verified, otherwise month','embedded month/date evidence'),Field('retrieved_at_utc','datetime',False,'Artifact capture time','acquisition receipt'),Field('source_artifact_id','string',False,'Original PDF bytes SHA256','raw archive'),Field('snapshot_id','string',False,'Parser/schema/config/source identity','normalized manifest'),Field('vintage_type','string',False,'report_vintage, never current API relabelled as historical','source PDF')]))
NUM=re.compile(r'^(?:[+−‐‑–-]?\d[\d,]*(?:\.\d+)?|nr|NR|--|—|N/A|NA|\[blank\])$')
YEARS=re.compile(r'\b(?:19|20)\d{2}/\d{2}\b')
MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']


def normalize(text):return ' '.join(text.split())


def numeric(token):
    if token=='[blank]':return None,'missing'
    if token.lower()=='nr':return None,'not_reported'
    if token in {'--','—','N/A','NA'}:return None,'not_applicable'
    if not NUM.fullmatch(token):raise FormatError('Unknown report numeric cell')
    try:return Decimal(token.replace(',','').replace('−','-').replace('‐','-').replace('‑','-').replace('–','-')),'reported'
    except InvalidOperation:raise FormatError('Invalid report decimal') from None


def tail(line,count):
    tokens=line.split()
    if len(tokens)>count and all(NUM.fullmatch(t) for t in tokens[-count:]):
        return normalize(' '.join(tokens[:-count])),tokens[-count:]
    return None


def header_periods(lines):
    for line in lines:
        found=YEARS.findall(line)
        if len(found)>=3 and "Proj" not in line and "Prel" not in line:return found
    raise FormatError('Missing report period header')


def report_period(pdf):
    from collections import Counter
    found=[]
    month_names='January|February|March|April|May|June|July|August|September|October|November|December'
    first_text=pdf.pages[0].extract_text(x_tolerance=1,y_tolerance=3) or ''
    if len(pdf.pages)==1:
        notice=re.search(r'not published in ('+month_names+r')\s+(20\d{2})',first_text,re.I)
        if notice:return datetime.strptime(notice[1]+' '+notice[2],'%B %Y').strftime('%Y-%m')
    masthead=[line['text'] for line in pdf.pages[0].extract_text_lines(return_chars=False) if line['top']<190 and re.fullmatch(r'('+month_names+r'),?\s+20\d{2}',line['text'])]
    if len(masthead)==1:return datetime.strptime(masthead[0].replace(',',''),'%B %Y').strftime('%Y-%m')
    for index in sorted(set([0,min(1,len(pdf.pages)-1),len(pdf.pages)-1])):
        page=pdf.pages[index]
        words=page.extract_words(x_tolerance=1,y_tolerance=3)
        zones=[' '.join(w['text'] for w in words if w['top']<190),' '.join(w['text'] for w in words if w['top']>page.height-100)]
        for text in zones:
            found.extend(re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(20\d{2})\b',text))
    if not found:raise FormatError('Cannot verify embedded report month')
    common=Counter(found).most_common()
    if len(common)>1 and common[0][1]==common[1][1]:raise FormatError('Ambiguous embedded publication month')
    month,year=common[0][0]
    return datetime.strptime(month+' '+year,'%B %Y').strftime('%Y-%m')


class Collector:
    def __init__(self,family,period,receipt,release_date=None):
        self.family=family;self.period=period;self.receipt=receipt;self.release_date=release_date
        self.records=[];self.metadata={};self.coverage=[];self.excluded=[];self.change_contexts={}

    def table(self,title,page,text,layout,mapping=None):
        metadata={'mapping_notes':mapping or {},'title':title,'source_page':page,'layout':layout,'complete_source_text':text,'unit_policy':'Preserve displayed quantity scale. Area columns use hectares at the table scale, yield uses the displayed yield unit, percentages and counts remain distinct. Cotton uses the report cotton-table bales denomination; no numeric conversion is applied.'}
        id=sha256(canonical(metadata));self.metadata[id]=metadata
        self.coverage.append({'report_family':self.family,'report_period':self.period,'table_title':title,'source_page':page,'required':True,'status':'separate_extraction','layout':layout,'input_cells':0,'metadata_id':id})
        return id

    def add(self,metadata_id,*,section,row,indicator,period,comparison,unit,value,page,line,commodity='not_applicable',product_type='not_applicable',basis='source-labelled period'):
        number,status=numeric(value)
        record=dict(report_family=self.family,report_period=self.period,table_title=self.metadata[metadata_id]['title'],section_label=section or 'not_applicable',section_product_type=product_type,row_label=row,column_commodity=commodity,indicator=indicator,period_label=period,comparison_label=comparison,unit=unit,value=number,raw_value=value,value_status=status,period_basis=basis,table_metadata_id=metadata_id,source_page=page,source_occurrences=1,source_locations=json.dumps([{'page':page,'line':line,'raw_value':value}]),source_release_date=self.release_date,source_release_at_utc=None,release_time_precision='day' if self.release_date else 'month',retrieved_at_utc=datetime.fromisoformat(self.receipt['retrieved_at_utc']),source_artifact_id=self.receipt['source_artifact_id'],snapshot_id='unpublished',vintage_type='report_vintage')
        if not all(record[k] for k in KEYS):raise ValidationError('Missing report business dimension')
        self.records.append(record)
        next(c for c in self.coverage if c['metadata_id']==metadata_id)['input_cells']+=1

    def finish(self):
        unique={};duplicates=[]
        for record in self.records:
            key=tuple(record[k] for k in KEYS)
            if key not in unique:unique[key]=record;continue
            first=unique[key]
            if first['value']!=record['value'] or first['value_status']!=record['value_status']:
                raise ValidationError(f'Conflicting source report duplicate; classifications need investigation: {dict(zip(KEYS,key))} values {first["value"]}/{record["value"]}')
            # Identical printed duplicates are explicitly retained as occurrence evidence.
            first['source_occurrences']+=1
            first['source_locations']=json.dumps(json.loads(first['source_locations'])+json.loads(record['source_locations']))
            duplicates.append({'business_key':dict(zip(KEYS,key)),'locations':json.loads(first['source_locations']),'reason':'Same dimensions and same displayed value repeat in original PDF; one business cell with all source occurrences retained.'})
        if any(c['input_cells']==0 for c in self.coverage):raise ValidationError('Required report table produced no cells: '+str([(c['table_title'],c['source_page']) for c in self.coverage if c['input_cells']==0]))
        frame=SCHEMA.frame(list(unique.values()))
        if sum(frame['source_occurrences'])!=len(self.records):raise ValidationError('Report source-cell accounting mismatch')
        return frame,{'tables':self.coverage,'input_cells':len(self.records),'unique_cells':len(frame),'duplicate_cells':len(self.records)-len(frame),'duplicate_evidence':duplicates,'excluded_lines':self.excluded,'metadata':self.metadata}


def printed_month_pair(lines,period):
    for line in lines[:10]:
        tokens=[t for t in line.split() if t in MONTHS]
        if len(tokens)>=2:return tokens[0],tokens[1]
    return month_pair(period)


def month_pair(period):
    index=int(period[-2:])-1
    return MONTHS[(index-1)%12],MONTHS[index]


def parse_wap_standard(collector,title,page,text,table_number,page_object=None):
    lines=text.splitlines();periods=next((YEARS.findall(line) for line in lines if len(YEARS.findall(line))>=2 and 'Proj' not in line and 'Prel' not in line),[]);previous,current=printed_month_pair(lines,collector.period)
    if len(periods)<2:raise FormatError(f'Missing WAP year header: {title}')
    header_line=next((line for line in lines if len(YEARS.findall(line))>=2 and 'Prel' not in line and 'Proj' not in line),None)
    header_months=[w for w in (header_line or '').split() if w in MONTHS]
    first_projection=len(header_months)==(1 if table_number==16 else 3)
    expected=(5 if table_number==16 else 11) if first_projection else (8 if table_number==16 else 16)
    years=periods[:2]+[next(y for y in reversed(periods) if y not in periods[:2])]*2 if len(set(periods))>=3 else periods[:2]+[str(int(collector.period[:4]))+'/'+str(int(collector.period[:4])+1)[-2:]]*2
    # Header year rows list only the two historical years. The projection year is
    # explicitly read from the preceding Proj. header instead of a calendar inference.
    projected=re.findall(r'((?:19|20)\d{2}/\d{2})\s+Proj',text)
    if not projected:raise FormatError('Missing WAP projected marketing-year label')
    years=periods[:2]+[projected[0]]*2
    id=collector.table(title,page,text,'wap-production-'+str(expected) if table_number==16 else 'wap-area-yield-production-'+str(expected));section='not_applicable';active=False
    if page_object is not None:
        lines=aligned_wap_lines(page_object,lines,expected)
    for n,line in enumerate(lines,1):
        parsed=tail(line,expected)
        if parsed and not YEARS.search(parsed[0]) and not parsed[0].startswith(('Prel.','Country','Foreign Agricultural')):
            row,values=parsed;active=True
            groups=['Production'] if table_number==16 else ['Area','Yield','Production']
            for group_index,metric in enumerate(groups):
                unit=('Million 1000 HA' if '(Million 1000 HA)' in text else 'Million hectares') if metric=='Area' else ('Kilograms per hectare' if table_number==17 else 'Metric tons per hectare') if metric=='Yield' else 'Million 480-lb. bales' if table_number==17 else 'Million metric tons'
                width=3 if first_projection else 4
                comparisons=['not_applicable','not_applicable',current] if first_projection else ['not_applicable','not_applicable',previous,current]
                for j in range(width):collector.add(id,section=section,row=row,indicator=metric,period=years[j],comparison=comparisons[j],unit=unit,value=values[group_index*width+j],page=page,line=n)
            changes=values[-2:] if first_projection else values[-4:]
            for j,value in enumerate(changes):collector.add(id,section=section,row=row,indicator='Change in Production from last month' if not first_projection and j<2 else 'Change in Production from last year',period=projected[0],comparison=current,unit='Percent' if j%2 else 'Million 480-lb. bales' if table_number==17 else 'Million metric tons',value=value,page=page,line=n)
        elif table_number==16 and line.startswith(('Oilseed,','Oil, key','Oil, Palm')):section=normalize(line)
        else:
            # Region-heading rows have no observations; footnotes are retained in metadata.
            if active and len(line.split())>5 and all(NUM.fullmatch(t) for t in line.split()[-5:]) and not line.startswith('Foreign Agricultural'):
                raise FormatError(f'Changed WAP numerical row width: {title}: {line}')
            collector.excluded.append({'page':page,'line':n,'reason':'header, grouping label, or source footnote'})


def parse_year_columns(collector,title,page,text,multi=False):
    lines=text.splitlines();periods=header_periods(lines);count=len(periods);previous,current=printed_month_pair(lines,collector.period)
    if count not in {6,9}:raise FormatError('Unsupported report year-column count')
    unit=next((normalize(l) for l in lines[:4] if 'Metric Tons' in l),None)
    if not unit and title=='All Grain Summary Comparison':unit='Million Metric Tons'
    if not unit:raise FormatError('Missing report unit caption')
    if ',' in unit and 'Years,' in unit:unit=unit.split('Years,',1)[1].strip()
    if 'Year,' in unit:unit=unit.split('Year,',1)[1].strip()
    basis=' | '.join(lines[1:3]);commodities=['not_applicable']*count
    if count==9:
        if title=='All Grain Summary Comparison':groups=['Wheat','Rice, Milled','Corn']
        else:
            header=next((l for l in lines[1:6] if len(re.findall(r'(?:Oilseed|Meal|Oil),',l))==3),None)
            if not header:raise FormatError('Missing commodity column groups')
            groups=[normalize(x) for x in re.findall(r'(?:Oilseed|Meal|Oil),.*?(?=(?:Oilseed|Meal|Oil),|$)',header)]
        if len(groups)!=3:raise FormatError('Ambiguous commodity column groups')
        commodities=[c for c in groups for _ in range(3)]
    id=collector.table(title,page,text,'year-columns-'+str(count));section='';product_type='not_applicable';active=False
    header_line=next(i for i,l in enumerate(lines) if len(YEARS.findall(l))==count)
    for i,line in enumerate(lines):
        if i<=header_line:continue
        parsed=tail(line,count)
        if parsed:
            row,values=parsed
            if not section:raise FormatError(f'Report numeric row has no indicator section: {title}: {line}')
            prefix=re.match(r'(Oilseed|Meal|Oil),',row)
            if prefix:product_type=prefix.group(1)
            for j,value in enumerate(values):
                comparison=previous if count==6 and j==4 else current if count==6 and j==5 else 'not_applicable'
                collector.add(id,section=section,row=row,indicator=section,period=periods[j],comparison=comparison,unit=unit,value=value,page=page,line=i+1,commodity=commodities[j],product_type=product_type,basis=basis)
            active=True
        else:
            label=normalize(line.removesuffix(' none'))
            if label in {'Production','Milled Production','Imports','Exports','Crush','Ending Stocks','Beginning Stocks','Total Consumption','Consumption and Residual','Domestic Consumption','TY Imports','TY Exports','Industrial Dom. Cons.','Food Use Dom. Cons.','SME','Consumption','Area Harvested'}:
                section=label;product_type='not_applicable'
            elif active and len(line.split())>count and all(NUM.fullmatch(t) for t in line.split()[-count+1:]):
                raise FormatError('Changed report numeric row width')
            else:collector.excluded.append({'page':page,'line':i+1,'reason':'header, grouping label, note or footer'})


def parse_history_columns(collector,title,page,text):
    lines=text.splitlines();unit=next((normalize(l) for l in lines[:4] if 'Metric Tons' in l),None)
    if not unit:raise FormatError('Missing historical table unit caption')
    first=next((i for i,l in enumerate(lines) if re.match(r'^\d{4}/\d{2}\s',l)),None)
    if first is None:raise FormatError('Historical table has no observation-year rows')
    heading=' '.join(lines[2:first-1]);metrics=[]
    if 'Area' in heading:metrics.append('Area Harvested')
    metrics+=['Beginning Stocks','Production','Imports']
    if 'Total' in heading:metrics.append('Total Supply')
    metrics.append('Exports')
    if 'Crush' in heading:metrics.append('Crush')
    if 'Industrial' in heading:metrics.append('Industrial Dom. Cons.')
    if 'Food Use' in heading:metrics.append('Food Use Dom. Cons.')
    metrics+=['Domestic Consumption','Ending Stocks']
    id=collector.table(title,page,text,'historical-attribute-columns');section=''
    for i,line in enumerate(lines):
        if i<first-1:continue
        if re.fullmatch(r'\d{4}/\d{2} MY\.',line):
            collector.excluded.append({'page':page,'line':i+1,'reason':'continuation of explicit marketing-year definition footnote'});continue
        if re.match(r'^\d{4}/\d{2}\s',line):
            tokens=line.split();period=tokens[0];values=tokens[1:]
            if not section or len(values)!=len(metrics) or not all(NUM.fullmatch(x) for x in values):raise FormatError(f'Changed historical report row layout: {title}: section={section!r}, metrics={metrics}, line={line}')
            for metric,value in zip(metrics,values):
                metric_unit=('Million hectares' if unit.startswith('Million') else 'Thousand hectares') if metric=='Area Harvested' else unit
                collector.add(id,section=section,row=period,indicator=metric,period=period,comparison='not_applicable',unit=metric_unit,value=value,page=page,line=i+1,basis='Local marketing years; original table country and commodity labels retained')
        elif line.startswith(('Major ','Oilseed,','Oil,','Meal,')) or line in {'Soybeans','Soybean Meal','Soybean Oil'}:section=normalize(line)
        else:collector.excluded.append({'page':page,'line':i+1,'reason':'header, source note or footer'})


def parse_wap_summary(collector,title,page,text,page_object=None):
    lines=text.splitlines();id=collector.table(title,page,text,'wap-summary-country-columns')
    geographies=['World','Total Foreign','United States','Canada','Mexico','Russia','Ukraine','European','China','India','Indonesia','Pakistan','Thailand','Argentina','Brazil','Australia','South Africa','Turkey','All Others']
    if page_object is not None:
        raw_words=page_object.extract_words(x_tolerance=1,y_tolerance=2);words=[]
        for word in raw_words:
            prior=words[-1] if words else None
            if prior and word['top']<115 and abs(prior['top']-word['top'])<1 and -.2<word['x0']-prior['x1']<.2:
                words[-1]={**prior,'text':prior['text']+word['text'],'x1':word['x1']}
            else:words.append(word)
        first_header=next((w for w in words if w['text']=='World' and 60<w['top']<90),None)
        if first_header is None:raise FormatError('Missing WAP summary geography header')
        anchors=sorted([w for w in words if abs(w['top']-first_header['top'])<1 and w['x0']>90],key=lambda w:w['x0'])
        if len(anchors) not in {18,19}:raise FormatError('Unknown WAP summary geography column layout')
        centers=[(w['x0']+w['x1'])/2 for w in anchors];geographies=[]
        for c,anchor in enumerate(anchors):
            column=[w for w in words if first_header['top']<=w['top']<first_header['top']+35 and min(range(len(anchors)),key=lambda j:abs(centers[j]-(w['x0']+w['x1'])/2))==c and w['x0']>90]
            bottom=[w['text'] for w in column if w['top']>first_header['top']+12 and w['text'] not in {'none','-'}]
            top=[w['text'] for w in column if w['top']<=first_header['top']+12 and w['text'] not in {'none','-'}]
            name=' '.join(bottom or top).replace('- ','')
            if name.endswith(' n'):name=name[:-2]+'n'
            geographies.append(name)
        replacements={}
        for line in page_object.extract_text_lines(x_tolerance=1,y_tolerance=3,return_chars=False):
            if line['top']>page_object.height-65 or 'Foreign Agricultural' in line['text'] or 'Office of' in line['text']:continue
            label_match=re.match(r'^(\d{4}/\d{2}(?: prel\.)?|'+ '|'.join(MONTHS)+r')\s+',line['text'])
            if not label_match or 'proj.' in line['text']:continue
            cell_words=[w for w in words if abs(w['top']-line['top'])<3 and (w['x0']+w['x1'])/2>centers[0]-15 and NUM.fullmatch(w['text'])]
            if len(cell_words)>=len(centers):continue
            values=['[blank]']*len(centers)
            for word in cell_words:
                j=min(range(len(centers)),key=lambda k:abs(centers[k]-(word['x0']+word['x1'])/2))
                if values[j]!='[blank]':raise FormatError('Ambiguous WAP summary numeric column alignment')
                values[j]=word['text']
            replacements[normalize(line['text'])]=label_match[1]+' '+' '.join(values)
        lines=[replacements.get(normalize(line),line) for line in lines]
    section='';projected=None
    for i,line in enumerate(lines):
        parsed=tail(line,len(geographies))
        if parsed:
            row,values=parsed
            if not section:raise FormatError('Missing WAP summary commodity')
            found=YEARS.search(row);period=found.group(0) if found else projected
            comparison=row if row in MONTHS else 'not_applicable'
            if not period:raise FormatError('Missing WAP summary source period')
            for geo,value in zip(geographies,values):collector.add(id,section=section,row=geo,indicator='Production',period=period,comparison=comparison,unit='Million 480-lb. bales' if section=='Cotton' else 'Million metric tons',value=value,page=page,line=i+1)
        elif line in {'Wheat','Coarse Grains','Rice, Milled','Total Grains','Oilseeds','Cotton'}:section=line
        elif re.fullmatch(r'\d{4}/\d{2}\s+proj\.',line,re.I):projected=YEARS.search(line).group(0)
        else:collector.excluded.append({'page':page,'line':i+1,'reason':'summary header or note'})


def parse_reliability(collector,title,page,text):
    lines=text.splitlines();id=collector.table(title,page,text,'production-reliability-seven-statistics')
    period_match=re.search(r'Marketing years\s+(\d{4}/\d{2})\s+through\s+(\d{4}/\d{2})',text,re.I)
    if not period_match:raise FormatError('Missing reliability evaluation-period definition')
    period=period_match.group(1)+' through '+period_match.group(2)
    metrics=['Root mean square error','90 percent confidence interval','Average difference','Smallest difference','Largest difference','Years below final','Years above final']
    section='';pending=None;us=False
    def add(label,values,line):
        commodity=label if us else section;region='United States' if us else label
        amount_unit='Million bushels' if us else 'Million 480-lb. bales' if section=='COTTON' else 'Million metric tons'
        for j,value in enumerate(values):collector.add(id,section=commodity,row=region,indicator=metrics[j],period=period,comparison='not_applicable',unit='Percent' if j<2 else 'Years' if j>=5 else amount_unit,value=value,page=page,line=line)
    for i,line in enumerate(lines):
        label=re.sub(r'\s+\d+/$','',line).strip()
        if label.startswith('UNITED STATES'):us=True;continue
        if not us and label.split('---')[0].strip() in {'WHEAT','COARSE GRAINS','RICE (Milled)','SOYBEANS','COTTON'}:section=label.split('---')[0].strip();continue
        tokens=line.split()
        if len(tokens)==7 and all(NUM.fullmatch(x) for x in tokens):
            if pending is not None:raise FormatError('Unpaired reliability numeric row')
            pending=tokens;continue
        if pending is not None and label in {'World','U.S.','Foreign','CORN','SORGHUM','BARLEY','OATS'}:
            add(label,pending,i+1);pending=None;continue
        parsed=tail(line,7)
        if parsed and parsed[0] in {'World','U.S.','Foreign','CORN','SORGHUM','BARLEY','OATS'}:add(*parsed,i+1)
        else:collector.excluded.append({'page':page,'line':i+1,'reason':'reliability heading/definition/note'})
    if pending is not None:raise FormatError('Unmatched reliability values')


def parse_change_segment_legacy(collector,page,text,words,descriptor,y0,y1,required=False):
    title,period,centers,default_commodity=descriptor
    names=list(centers);labels=dict(collector.change_contexts.get(title,{'Country':'','Commodity':default_commodity,'Attribute':''}));previous_column=None
    left=min(centers.values())-65;right=(centers['Change']+centers.get('Reason',centers['Change']+80))/2
    anchors=[];numeric_words=[]
    for index,word in enumerate(words):
        if not y0<=word['top']<y1:continue
        center=(word['x0']+word['x1'])/2
        if not left<=center<right:previous_column=None;continue
        column=min(names,key=lambda name:abs(centers[name]-center));token=word['text']
        if column in {'Country','Commodity','Attribute'}:
            if previous_column!=column or column=='Attribute':labels[column]=token
            else:labels[column]+=' '+token
            previous_column=column
            if column=='Attribute' and token in {'Imports','Exports','Production','Crush','Consumption'}:
                if not all(labels.values()):raise FormatError(f'Missing merged-cell country/commodity/attribute label: {title}, page {page}, labels={labels}, top={word["top"]}')
                anchors.append({'top':word['top'],'labels':dict(labels),'values':{},'line':index})
        elif column in {'Previous','Current','Change'} and NUM.fullmatch(token):
            numeric_words.append((column,word,index));previous_column=column
        else:previous_column=None
    if not anchors:
        if required:raise FormatError('Printed changes-table header has no data indicator rows')
        collector.excluded.append({'page':page,'reason':'No continuation data anchors or numeric cells; administrative/header text'})
        return
    id=collector.table(title,page,text,'trade-outlook-changes')
    for column,word,index in numeric_words:
        if word['top']>max(a['top'] for a in anchors)+4 or word['top']<min(a['top'] for a in anchors)-4:
            collector.excluded.append({'page':page,'word_index':index,'reason':'Numeric text outside verified changes-table indicator-row vertical extent; source notes/contacts are not data'})
            continue
        if not anchors:raise FormatError('Changes values have no indicator row anchors')
        anchor=min(anchors,key=lambda row:abs(row['top']-word['top']))
        if abs(anchor['top']-word['top'])>3 or column in anchor['values']:
            raise FormatError(f'Changes-table numeric coordinate mismatch: {title}, page {page}, word={word["text"]} top={word["top"]}, column={column}, nearest={anchor}')
        anchor['values'][column]=word['text']
    collector.change_contexts[title]=dict(labels)
    for anchor in anchors:
        if set(anchor['values'])!={'Previous','Current','Change'}:raise FormatError(f'Incomplete changes-table numeric row: {title}, page={page}, anchor={anchor}')
        row=anchor['labels']
        for comparison,value in anchor['values'].items():collector.add(id,section=row['Attribute'],row=normalize(row['Country']),indicator=row['Attribute'],period=period,comparison=comparison,unit='Thousand Metric Tons',value=value,page=page,line=anchor['line'],commodity=normalize(row['Commodity']),basis='Trade-year label as printed' if collector.family=='grain-trade' else 'Source marketing-year outlook label')


def parse_change_segment(collector,page,text,words,descriptor,y0,y1,required=False,page_object=None):
    """Resolve merged labels using printed horizontal rules and numeric row baselines."""
    if page_object is None:
        return parse_change_segment_legacy(collector,page,text,words,descriptor,y0,y1,required)
    title,period,centers,default_commodity=descriptor
    names=list(centers);label_bounds=getattr(centers,'bounds',{})
    administrative=[line['top'] for line in page_object.extract_text_lines(return_chars=False) if y0<line['top']<y1 and re.match(r'Questions may|To download|For further information|The Foreign Agricultural|FAS Reports and|Oilseeds HS Codes|HS Codes|Note:',line['text'])]
    if administrative:y1=min(administrative)
    left=min(centers.values())-65
    right=(centers['Change']+centers.get('Reason',centers['Change']+80))/2
    segment_lines=[line for line in page_object.extract_text_lines(return_chars=False) if y0<=line['top']<y1]
    if any(re.search(r'No (?:forecast |significant |major )?changes',line['text'],re.I) for line in segment_lines):
        collector.excluded.append({'page':page,'table_title':title,'reason':'Printed source explicitly reports no changes','source_text':' '.join(line['text'] for line in segment_lines)})
        return
    all_words=[]
    for word in page_object.extract_words(x_tolerance=3,y_tolerance=2):
        prefix=re.match(r'^([+-]?\d[\d,]*(?:\.\d+)?)(?=[A-Za-z])',word['text'])
        if prefix and centers['Current']<word['x0']<centers.get('Reason',centers['Change']+80):
            chars=sorted([c for c in page_object.chars if abs(c['top']-word['top'])<2 and word['x0']-.1<=c['x0']<word['x1']],key=lambda c:c['x0'])
            if ''.join(c['text'] for c in chars).startswith(prefix[1]):word={**word,'text':prefix[1],'x1':chars[len(prefix[1])-1]['x1']}
        previous=all_words[-1] if all_words else None
        if previous and abs(previous['top']-word['top'])<2 and -3<word['x0']-previous['x1']<3 and re.fullmatch(r'[-−\d,.]+',previous['text']) and re.fullmatch(r'[\d,.]+',word['text']) and NUM.fullmatch(previous['text']+word['text']):
            all_words[-1]={**previous,'text':previous['text']+word['text'],'x1':word['x1']}
        else:all_words.append(word)
    if 'Attribute' in centers:
        actual_attributes=[w for w in all_words if y0<=w['top']<y1 and w['text'] in {'Imports','Exports','Import','Export'} and abs(w['x0']-centers['Attribute'])<45]
        if actual_attributes:
            edge=min(w['x0'] for w in actual_attributes)-3
            left_name='Commodity' if 'Commodity' in centers else 'Country'
            label_bounds={**label_bounds,left_name:(label_bounds.get(left_name,(left,edge))[0],edge),'Attribute':(edge,(centers['Attribute']+centers['Previous'])/2)}
    selected=[w for w in all_words
              if y0<=w['top']<y1 and left<=(w['x0']+w['x1'])/2<right]
    def column(w):
        if not NUM.fullmatch(w['text']):
            for name in ['Country','Commodity','Attribute']:
                if name in label_bounds and label_bounds[name][0]<=(w['x0']+w['x1'])/2<label_bounds[name][1]:return name
        return min(names,key=lambda n:abs(centers[n]-(w['x0']+w['x1'])/2))
    candidate_words=[w for w in all_words if y0<=w['top']<y1 and centers['Attribute']+20<w['x0']<centers.get('Reason',right)+15 and NUM.fullmatch(w['text'])]
    candidate_rows=[]
    for w in sorted(candidate_words,key=lambda w:(w['top'],w['x0'])):
        if not candidate_rows or abs(w['top']-candidate_rows[-1][0]['top'])>3:candidate_rows.append([w])
        else:candidate_rows[-1].append(w)
    complete=next((sorted(row,key=lambda w:w['x0']) for row in candidate_rows if len(row)==3),None)
    if complete:
        centers=dict(centers)
        numeric_names=sorted(['Previous','Current','Change'],key=lambda n:centers[n])
        for name,w in zip(numeric_names,complete):centers[name]=w['x1']-10
        centers['Reason']=max(centers.get('Reason',0),complete[-1]['x1']+30)
        right=complete[-1]['x1']+10
        all_words=[]
    for word in page_object.extract_words(x_tolerance=3,y_tolerance=2):
        prefix=re.match(r'^([+-]?\d[\d,]*(?:\.\d+)?)(?=[A-Za-z])',word['text'])
        if prefix and centers['Current']<word['x0']<centers.get('Reason',centers['Change']+80):
            chars=sorted([c for c in page_object.chars if abs(c['top']-word['top'])<2 and word['x0']-.1<=c['x0']<word['x1']],key=lambda c:c['x0'])
            if ''.join(c['text'] for c in chars).startswith(prefix[1]):word={**word,'text':prefix[1],'x1':chars[len(prefix[1])-1]['x1']}
        previous=all_words[-1] if all_words else None
        if previous and abs(previous['top']-word['top'])<2 and -3<word['x0']-previous['x1']<3 and re.fullmatch(r'[-−\d,.]+',previous['text']) and re.fullmatch(r'[\d,.]+',word['text']) and NUM.fullmatch(previous['text']+word['text']):
            all_words[-1]={**previous,'text':previous['text']+word['text'],'x1':word['x1']}
        else:all_words.append(word)
    selected=[w for w in all_words if y0<=w['top']<y1 and left<=(w['x0']+w['x1'])/2<right]
    attribute_words=[w for w in selected if column(w)=='Attribute' and w['text'].replace(' ','') in {'Import','Imports','Export','Exports','Production','Crush','Consumption'}]
    if not attribute_words and not required:
        collector.excluded.append({'page':page,'reason':'No changes-table attribute rows in continuation region'})
        return
    if attribute_words:
        lo=min(w['top'] for w in attribute_words)-15;hi=max(w['bottom'] for w in attribute_words)+15
        selected=[w for w in selected if not NUM.fullmatch(w['text']) or lo<=w['top']<=hi]
    numbers=[w for w in selected if column(w) in {'Previous','Current','Change'} and NUM.fullmatch(w['text'])]
    rows=[]
    for word in sorted(numbers,key=lambda w:(w['top'],w['x0'])):
        if not rows or abs(word['top']-rows[-1]['top'])>3:
            rows.append({'top':word['top'],'bottom':word['bottom'],'values':{}})
        row=rows[-1];name=column(word)
        if name in row['values']:raise FormatError(f'Ambiguous repeated changes-table numeric column: {title}, page={page}, word={word}, row={row}, centers={centers}')
        row['values'][name]=word['text']
    # Administrative contact pages contain indicator words but no numeric grid.
    if not rows:
        if required:raise FormatError('Printed changes-table header has no numeric rows')
        collector.excluded.append({'page':page,'reason':'No numerical changes grid on continuation page'})
        return
    edges=[e for e in page_object.edges if e['height']<1 and e['width']>15 and e['object_type']!='rect_edge']
    def white(color):return color==1 or isinstance(color,(list,tuple)) and all(v==1 for v in color)
    colored=any(isinstance(r.get('non_stroking_color'),tuple) and len(set(r['non_stroking_color']))>1 for r in page_object.rects if y0<=r['top']<y1)
    edges += [r for r in page_object.rects if r['height']<2 and r['width']>15 and (colored or not white(r.get('non_stroking_color')))]
    contexts=collector.change_contexts.get(title,{})
    id=collector.table(title,page,text,'trade-outlook-changes')
    for index,row in enumerate(rows):
        if set(row['values'])!={'Previous','Current','Change'}:
            raise FormatError(f'Incomplete changes-table numeric columns: {title}, page={page}, row={row}')
        labels={}
        midpoint=(row['top']+row['bottom'])/2
        for name in ['Country','Commodity','Attribute']:
            if name not in centers:
                labels[name]=default_commodity
                continue
            rules=sorted({e['top'] for e in edges if e['x0']-2<=centers[name]<=e['x1']+2 and y0-15<=e['top']<=y1})
            upper=max((v for v in rules if v<midpoint),default=y0)
            lower=min((v for v in rules if v>midpoint),default=y1)
            backgrounds=[r for r in page_object.rects if colored and r['x0']<=centers[name]<=r['x1'] and r['top']<=midpoint<=r['bottom'] and 5<r['height'] and r['width']<180 and isinstance(r.get('non_stroking_color'),tuple) and len(set(r['non_stroking_color']))>1]
            if backgrounds:
                cell=max(backgrounds,key=lambda r:r['height']*r['width']);upper=max(y0,cell['top']);lower=min(y1,cell['bottom'])
            tokens=sorted([w for w in selected if column(w)==name and upper<=((w['top']+w['bottom'])/2)<lower],key=lambda w:(round(w['top']/3),w['x0']))
            value=normalize(' '.join(w['text'] for w in tokens))
            if name=='Commodity' and collector.family=='grain-trade' and len(tokens)>1 and all(w['text'] in {'Wheat','Corn','Barley','Sorghum','Oats','Rye','Rice'} for w in tokens):
                nearest=min(tokens,key=lambda w:abs(w['top']-row['top']))
                if abs(nearest['top']-row['top'])<=3:value=nearest['text']
            if name=='Attribute' and len(tokens)>1:
                nearest=min(tokens,key=lambda w:abs(w['top']-row['top']))
                if abs(nearest['top']-row['top'])<=3:
                    pieces=[w['text'] for w in tokens if abs(w['top']-nearest['top'])<2]
                    joined=''.join(pieces)
                    value=joined if joined in {'Import','Imports','Export','Exports','Production','Crush','Consumption'} else nearest['text']
            if not value and (upper==y0 or index==0 or name=='Country' and y0==0 or name=='Commodity' and labels.get('Country')==contexts.get('Country')):value=contexts.get(name,'')
            labels[name]=value
        if labels['Attribute'] not in {'Import','Imports','Export','Exports','Production','Crush','Consumption'} or not all(labels.values()):
            raise FormatError(f'Unresolved changes-table merged labels: {title}, page={page}, row={index}, labels={labels}')
        for comparison,value in row['values'].items():
            collector.add(id,section=labels['Attribute'],row=labels['Country'],indicator=labels['Attribute'],period=period,comparison=comparison,unit='Thousand Metric Tons',value=value,page=page,line=index,commodity=labels['Commodity'],basis='Trade-year label as printed' if collector.family=='grain-trade' else 'Source marketing-year outlook label')
        contexts=labels
    collector.change_contexts[title]=contexts


class ColumnCenters(dict):
    def __init__(self,values,bounds):
        super().__init__(values);self.bounds=bounds


def change_descriptors(page,text,section,prior=None):
    words=page.extract_words(x_tolerance=1,y_tolerance=2,use_text_flow=True)
    lines=page.extract_text_lines(x_tolerance=1,y_tolerance=3,return_chars=False)
    result=[]
    for word in words:
        if word['text']!='Previous':continue
        header={w['text']:w for w in words if abs(w['top']-word['top'])<2 and w['text'] in {'Country','Commodity','Attribute','Previous','Current','Change','Reason'}}
        if not {'Country','Attribute','Current','Change'}<=set(header):continue
        candidates=[line for line in lines if line['top']<word['top'] and re.search(r'TRADE CHANGES|OUTLOOK CHANGES',line['text'],re.I) and re.search(r'\b20\d{2}\b',line['text'])]
        if not candidates:
            if prior is None:raise FormatError('Changes table header lacks a source period/title on page: '+text[:300])
            line={'top':0,'text':prior[0]}
        else:line=max(candidates,key=lambda l:l['top'])
        title=normalize(line['text'].split(' – ')[0])
        match=re.search(r'\b\d{4}(?:/\d{2})?\b',title)
        if not match:raise FormatError('Printed changes heading lacks an explicit source year: '+title)
        period=match.group(0)
        if 'TRADE CHANGES' in title.upper() and section:title=section+' | '+title
        centers={name:(w['x0']+w['x1'])/2 for name,w in sorted(header.items(),key=lambda x:x[1]['x0'])}
        order=sorted(header,key=lambda name:header[name]['x0'])
        bounds={name:((centers[order[i-1]]+centers[name])/2 if i else header[name]['x0']-65,(centers[name]+centers[order[i+1]])/2 if i+1<len(order) else page.width) for i,name in enumerate(order)}
        for name,word in header.items():
            cells=[r for r in page.rects if r['x0']<=word['x0'] and r['x1']>=word['x1'] and r['top']<=word['top'] and r['bottom']>=word['bottom'] and 15<r['width']<200 and r['height']>5]
            if cells:
                cell=max(cells,key=lambda r:r['width']);bounds[name]=(cell['x0'],cell['x1'])
        centers=ColumnCenters(centers,bounds)
        result.append({'title_top':line['top'],'data_top':max(w['bottom'] for w in header.values())+1,'descriptor':(title,period,centers,section.title() if 'Commodity' not in header else '')})
    ordered=sorted(result,key=lambda x:x['data_top']);deduplicated=[]
    for item in ordered:
        if deduplicated and item['title_top']==deduplicated[-1]['title_top'] and item['data_top']-deduplicated[-1]['data_top']<30:
            deduplicated[-1]=item
        else:deduplicated.append(item)
    return deduplicated,words


def identity(title):
    title=re.sub(r'\((?:Jan-Dec|Feb-Jan|Apr-Mar|Sep-Aug|Working Statistics)\)','',title)
    title=title.replace('World:','World').replace('South East Asia:','South East Asia').replace('European Union (27):','European Union').replace('Local Marketing Years','Local Marketing Year')
    title=title.replace(' Local Marketing Year','')
    title=title.replace('Minor Vegetable Oil Supply','Minor Vegetable Oils: World Supply').replace('Products World Supply','Products: World Supply')
    title=re.sub(r'\b\d{4}/\d{2}\b','<marketing-year>',title)
    title=re.sub(r'\b\d{4}\b','<year>',title)
    return normalize(title).lower()


def parse_report(body,family,receipt,*,expected_period=None,release_date=None):
    if family not in {'world-production','grain-trade','oilseed-trade'}:raise FormatError('Unknown FAS report family')
    with pdfplumber.open(io.BytesIO(body)) as pdf:
        period=report_period(pdf)
        if expected_period and expected_period!=period:raise ValidationError('Embedded report month differs from manifest')
        first_text=pdf.pages[0].extract_text(x_tolerance=1,y_tolerance=3) or ''
        if len(pdf.pages)==1 and 'not published' in first_text and 'lapse in' in first_text:
            return SCHEMA.frame([]),{'tables':[],'input_cells':0,'unique_cells':0,'duplicate_cells':0,'duplicate_evidence':[],'excluded_lines':[],'metadata':{},'source_unavailable':{'reason':'Official original report attachment explicitly states report was not published because of lapse in Federal funding','source_text':first_text,'source_artifact_id':receipt['source_artifact_id'],'report_period':period}}
        collector=Collector(family,period,receipt,release_date);active_changes=None;grain_section='' 
        for page_number,page in enumerate(pdf.pages,1):
            try:
                text=page.extract_text(x_tolerance=1,y_tolerance=3) or '';lines=text.splitlines();first=lines[0] if lines else ''
                if re.search(r'Avg\.? Price',text) and 'Export Prices' in text:parse_monthly_price_summaries(collector,page_number,page)
                if first in {'WHEAT','RICE','COARSE GRAINS'} or first.split(':')[0] in {'WHEAT','RICE','COARSE GRAINS'}:grain_section=first.split(':')[0];active_changes=None
                if family=='grain-trade':
                    footer=''.join(w['text'] for w in page.extract_words() if w['top']>page.height-100)
                    topic=re.search(r'(Wheat|Rice|CoarseGrains)Page\d+',footer,re.I)
                    if not topic:
                        topic=re.search(r'(Wheat|Rice|CoarseGrains)Page',footer,re.I)
                    if topic:grain_section={'wheat':'WHEAT','rice':'RICE','coarsegrains':'COARSE GRAINS'}[topic[1].lower()]
                if 'EXPORT PRICES' in first.upper() or re.fullmatch(r'20\d{2}/\d{2} OUTLOOK',first):active_changes=None
                if first.startswith(('ENDNOTES','OTHER NOTES','List of Tables','DATA TABLES','Questions may','FAS Reports and Databases','For further information','Oilseeds HS Codes','HS Codes')):active_changes=None
                numbered=re.match(r'Table\s+(\d{1,2})\b',first,re.I)
                grain_table=family=='grain-trade' and (first=='All Grain Summary Comparison' or re.match(r'(World|Regional) .*(Trade|Stocks)(?: \(Working Statistics\))?$',first))
                historical_grain=family=='grain-trade' and any(x in first for x in ['Supply and Demand','Supply and Disappearance','Grains Supply and Distribution'])
                if historical_grain:
                    active_changes=None;parse_legacy_grain_history(collector,first,page_number,text);continue
                if len(re.findall(r'^Table\s+\d',text,re.M))>=3 and not YEARS.search(text):
                    collector.excluded.append({'page':page_number,'reason':'Continuation of printed table of contents; actual required numerical tables are verified separately'})
                    continue
                if numbered or grain_table:
                    active_changes=None
                    if family=='world-production':
                        n=int(numbered.group(1))
                        if n==1:parse_wap_summary(collector,first,page_number,text,page)
                        elif n==18:
                            if 'Root mean' in text:parse_reliability(collector,'TABLE 18 Reliability of Production Projections',page_number,text)
                            else:parse_legacy_reliability(collector,'TABLE 18 Reliability of Production Projections',page_number,text)
                        elif 2<=n<=17:parse_wap_standard(collector,first,page_number,text,n,page)
                        else:raise FormatError('Unknown WAP numerical table family')
                    elif family=='oilseed-trade' and 29<=int(numbered.group(1))<=31:parse_price_table(collector,first,page_number,text,int(numbered.group(1)))
                    elif family=='oilseed-trade' and 15<=int(numbered.group(1))<=23:parse_history_columns(collector,first,page_number,text)
                    else:parse_year_columns(collector,first,page_number,text)
                    continue
                if 'Soybean Meal Trade Revisions for India and Bangladesh' in text:
                    parse_india_bangladesh_revisions(collector,page_number,page,text);active_changes=None;continue
                descriptors,words=change_descriptors(page,text,grain_section,active_changes)
                if active_changes and family=='oilseed-trade' and not first.startswith(('ENDNOTES','OTHER NOTES','List of Tables')):
                    stop=descriptors[0]['title_top'] if descriptors else page.height-60
                    # Continuations begin with a country/commodity row. An unrelated page
                    # cannot silently inherit a preceding changes table.
                    if re.search(r'\b(?:Imports|Exports|Production)\b',' '.join(w['text'] for w in words if w['top']<stop)):parse_change_segment(collector,page_number,text,words,active_changes,0,stop,page_object=page)
                for j,desc in enumerate(descriptors):
                    stop=descriptors[j+1]['title_top'] if j+1<len(descriptors) else page.height-60
                    parse_change_segment(collector,page_number,text,words,desc['descriptor'],desc['data_top'],stop,required=True,page_object=page)
                    active_changes=desc['descriptor']
            finally:
                page.close()
        frame,evidence=collector.finish()
    pinned_gaps=json.loads(Path(__file__).with_name('report_source_gaps.json').read_text())
    gap=pinned_gaps.get(sha256(body))
    if gap:
        if gap['family']!=family or gap['report_period']!=period:raise ValidationError('Source gap evidence dimensions differ')
        evidence['source_table_gaps']=[gap]
    if family=='grain-trade':
        evidence['summary_unit_checks']=verify_grain_summary_unit(frame,evidence)
    # A strict known table-family inventory, not a count of whatever happened to parse.
    from collections import Counter
    inventory=json.loads(Path(__file__).with_name('report_table_inventory.json').read_text())
    required=Counter(identity(t['table_title']) for t in inventory['tables'] if t['family']==family and t['required'])
    observed=Counter(identity(title) for title in {t['table_title'] for t in evidence['tables'] if t['layout'] not in {'monthly-export-price-summary','source-specific-trade-revision-years'}})
    # Changes tables depend on actual monthly changes. A missing printed changes
    # grid is not a missing appendix table. Each printed header must be parsed;
    # independently fixed numbered/main appendix families remain mandatory.
    required=Counter({k:v for k,v in required.items() if 'changes' not in k})
    observed_appendix=Counter({k:v for k,v in observed.items() if 'changes' not in k})
    unknown=set(observed_appendix)-set(required)
    if family=='oilseed-trade':unknown-={'table 29: oilseed prices','table 30: protein meal prices','table 31: vegetable oil prices'}
    if period<'2020-01':
        # Older verified layouts have additional historical/price tables and body
        # changes expressed as prose; never require nonexistent modern change grids.
        if family=='world-production':
            numbers={int(re.match(r'Table\s+(\d+)',t['table_title'],re.I).group(1)) for t in evidence['tables'] if re.match(r'Table\s+(\d+)',t['table_title'],re.I)}
            if gap:numbers.add(gap['missing_table_number'])
            if numbers!=set(range(1,19)):raise ValidationError('Incomplete historical WAP numbered tables')
        elif family=='oilseed-trade':
            numbers={int(re.match(r'Table\s+(\d+)',t['table_title']).group(1)) for t in evidence['tables'] if re.match(r'Table\s+(\d+)',t['table_title'])}
            if numbers!=set(range(1,32)):raise ValidationError('Incomplete historical oilseed tables including prices')
        else:
            main=[t for t in evidence['tables'] if t['layout'].startswith('year-columns')]
            if len(main)!=25:raise ValidationError('Incomplete historical grain main tables')
            if period<'2012-01' and not any(t['layout']=='legacy-grain-attribute-columns' for t in evidence['tables']):raise ValidationError('Missing required historical grain appendix')
        return frame,evidence
    if required-observed_appendix or unknown:
        raise ValidationError(f'Required report table coverage differs: missing={dict(required-observed)}, unexpected_types={sorted(unknown)}')
    return frame,evidence


def parse_legacy_reliability(collector,title,page,text):
    lines=text.splitlines();match=re.search(r'ESTIMATES,\s*(\d{4}/\d{2})\s*-\s*(\d{4}/\d{2})',text)
    if not match:raise FormatError('Unverified legacy reliability period')
    period=match[1]+' through '+match[2];id=collector.table(title,page,text,'legacy-reliability-six-statistics');section='';us=False
    metrics=['Average difference percent','Average difference','Lowest difference','Highest difference','Years below final','Years above final']
    for i,line in enumerate(lines,1):
        label=re.sub(r'\s+\d+/$','',line).strip()
        if label.startswith('UNITED STATES'):us=True;continue
        if label in {'WHEAT','COARSE GRAINS','RICE (Milled)','SOYBEANS','COTTON'}:section=label;continue
        parsed=tail(line,6)
        if parsed and parsed[0] in {'World','U.S.','Foreign','CORN','SORGHUM','BARLEY','OATS'}:
            region,values=parsed;commodity=region if us else section;region='United States' if us else region
            for j,value in enumerate(values):collector.add(id,section=commodity,row=region,indicator=metrics[j],period=period,comparison='not_applicable',unit='Percent' if j==0 else 'Years' if j>=4 else 'Million bushels' if us else 'Million 480-lb. bales' if section=='COTTON' else 'Million metric tons',value=value,page=page,line=i)
        else:collector.excluded.append({'page':page,'line':i,'reason':'legacy reliability heading/footnote'})


def parse_legacy_grain_history(collector,title,page,text):
    lines=text.splitlines();start=next((i for i,l in enumerate(lines) if re.match(r'^\d{4}/\d{2}\s',l)),None)
    if start is None:raise FormatError('Historical grain table has no period rows')
    caption=' '.join(lines[1:4]);header=' '.join(lines[2:start]);metrics=['Area Harvested','Yield']
    if 'Rough' in header:metrics.append('Rough Production')
    metrics.append('Production')
    if 'Imports' in header:metrics.append('MY Imports')
    if 'TY Imports' in header:metrics.append('TY Imports')
    if 'Exports' in header:
        if 'MY' in header or 'Imports' in header:metrics.append('MY Exports')
        if 'TY Exports' in header or 'MY' not in header and 'Imports' not in header:metrics.append('TY Exports')
    if 'Feed' in header:metrics.append('Feed Domestic Consumption' if 'Feed Dom.' in header else 'Feed and Residual')
    metrics+=['Domestic Consumption','Ending Stocks']
    id=collector.table(title,page,text,'legacy-grain-attribute-columns');section='';count=len(metrics)
    for i,line in enumerate(lines):
        parsed=tail(line,count)
        if parsed and re.fullmatch(r'\d{4}/\d{2}',parsed[0]):
            period,values=parsed
            if not section:raise FormatError('Missing historical grain geographic/commodity section')
            for metric,value in zip(metrics,values):
                unit='Metric tons per hectare' if metric=='Yield' else ('Thousand hectares' if caption.startswith('Thousand') else 'Million hectares') if metric=='Area Harvested' else 'Thousand Metric Tons' if caption.startswith('Thousand') else 'Million Metric Tons'
                collector.add(id,section=section,row=period,indicator=metric,period=period,comparison='not_applicable',unit=unit,value=value,page=page,line=i+1,basis=caption)
        elif i>=start-1:
            if re.match(r'^\d{4}/\d{2}\s',line):raise FormatError('Changed historical grain numeric width')
            if line.startswith(('Notes:','Note:','Foreign Agricultural','Office of','Grain:')):break
            if line.strip() and (not any(ch.isdigit() for ch in line) or re.fullmatch(r'.*Union - 12|EU-\d+',line)):section=normalize(line)
            collector.excluded.append({'page':page,'line':i+1,'reason':'legacy grain section/header/note'})


def parse_price_table(collector,title,page,text,table_number):
    """Retain original quote definitions by numbered source footnote, not a column index."""
    lines=text.splitlines();header=next((l for l in lines if l.startswith('Oct 1 ')),None)
    quotes=[int(v) for v in re.findall(r'(\d+)/',header or '')]
    if not quotes or quotes!=list(range(1,max(quotes)+1)):raise FormatError('Unknown price quote header')
    count=len(quotes)
    if count not in ({11} if table_number==29 else {9} if table_number==30 else {12,13}):raise FormatError('Unknown price quote count')
    # These identifiers are actual numbered report quote definitions (not arbitrary
    # positional keys). Full place/grade/FOB/CIF/source definitions live in metadata.
    available={int(n) for n in re.findall(r'(?<!\d)(\d{1,2})/',text)}
    if not set(range(1,count+1))<=available:raise FormatError('Price table lacks required quote definition footnotes')
    repairs=json.loads(Path(__file__).with_name('report_dimension_repairs.json').read_text())
    repair=repairs.get(collector.receipt['source_artifact_id'])
    if isinstance(repair,list):repair=next((r for r in repair if r['table_title']==title),None)
    if repair and title!=repair['table_title']:repair=None
    id=collector.table(title,page,text,'legacy-oilseed-price-quotes',mapping=repair);section='Oct-Sep average';year=None;active=False;year_counts={}
    for i,line in enumerate(lines,1):
        if re.match(r'^1/\s',line) and active:break
        parsed=tail(line,count)
        if parsed:
            label,values=parsed
            if label.startswith(('Oct 1','Year','Beg')):continue
            if YEARS.fullmatch(label) or re.fullmatch(r'\d{2}/\d{2}-\d{2}/\d{2}',label):period=label;comparison='annual_average'
            elif label.lstrip('*').strip() in MONTHS or label=='Average':
                if year is None:raise FormatError('Price month lacks source marketing year')
                period=year;comparison=label
            else:raise FormatError('Unknown price period label: '+label)
            for j,value in enumerate(values,1):collector.add(id,section='price_quotes',row=f'Source quote {j}/',indicator='Price',period=period,comparison=comparison,unit='U.S. Dollars per Metric Ton',value=value,page=page,line=i,basis='Source October-September marketing year; original numbered location/quality quotes and notes preserved')
            active=True
        elif YEARS.fullmatch(line):
            year_counts[line]=year_counts.get(line,0)+1;year=line
            if repair and line==repair['original_year'] and year_counts[line]==repair['occurrence']:
                following=next((l.lstrip('*') for l in lines[i:] if l.lstrip('*').startswith('Oct ')),None)
                if following!=repair['matching_first_row']:raise ValidationError('Pinned source header repair no longer matches original row')
                year=repair['normalized_year']
        elif active and line.lstrip('*') in MONTHS:
            if not year:raise FormatError('Missing year for blank quote row')
            for j in range(1,count+1):collector.add(id,section='price_quotes',row=f'Source quote {j}/',indicator='Price',period=year,comparison=line,unit='U.S. Dollars per Metric Ton',value='nr',page=page,line=i,basis='Source blank monthly price cells; month retained, not zero')
        else:collector.excluded.append({'page':page,'line':i,'reason':'price header/quote-definition note'})


def aligned_wap_lines(page,lines,expected):
    """Recover true blank cells by their verified right-aligned source columns."""
    words=page.extract_words(x_tolerance=1,y_tolerance=2)
    groups=[]
    for word in sorted(words,key=lambda w:(w['top'],w['x0'])):
        if not groups or abs(word['top']-groups[-1][0]['top'])>2:groups.append([word])
        else:groups[-1].append(word)
    anchors=None
    for group in groups:
        group=sorted(group,key=lambda w:w['x0']);numbers=[w for w in group if NUM.fullmatch(w['text'])]
        label=' '.join(w['text'] for w in group if not NUM.fullmatch(w['text']))
        if len(numbers)==expected and label and not YEARS.search(label):
            anchors=[w['x1'] for w in numbers];break
    if anchors is None:return lines
    replacements={}
    for group in groups:
        if group[0]['top']>page.height-45:continue
        group=sorted(group,key=lambda w:w['x0']);text=' '.join(w['text'] for w in group)
        numbers=[w for w in group if NUM.fullmatch(w['text']) and w['x1']>=anchors[0]-12]
        label=' '.join(w['text'] for w in group if w['x1']<anchors[0]-12)
        if not label or len(numbers)<1 or len(numbers)>=expected or YEARS.search(label):continue
        if any(k in label for k in ['Foreign Agricultural','Office of','Global Market','Prel.','MMT','Year','Note:']):continue
        values=['[blank]']*expected
        for w in numbers:
            j=min(range(expected),key=lambda i:abs(anchors[i]-w['x1']))
            if abs(anchors[j]-w['x1'])>3 or values[j]!='[blank]':break
            values[j]=w['text']
        else:replacements[normalize(text)]=normalize(label)+' '+' '.join(values)
    return [replacements.get(normalize(line),line) for line in lines]


def parse_monthly_price_summaries(collector,page_number,page):
    """Read actual monthly price-summary tables, excluding adjacent chart axes."""
    lines=page.extract_text_lines(x_tolerance=1,y_tolerance=3,return_chars=False)
    words=page.extract_words(x_tolerance=1,y_tolerance=2)
    titles=[l for l in lines if re.search(r'\b20\d{2}\b.*Export Prices',l['text'])]
    for ti,title in enumerate(titles):
        next_title=titles[ti+1]['top'] if ti+1<len(titles) else page.height
        average=next((l for l in lines if title['bottom']<l['top']<next_title and re.search(r'Avg\.? Price',l['text'])),None)
        if average is None:continue
        change=next((l for l in lines if average['bottom']<l['top']<next_title and l['text'].startswith('Change vs')),None)
        if change is None:raise FormatError('Monthly price summary missing its printed change row')
        price_words=[w for w in words if abs(w['top']-average['top'])<3 and re.fullmatch(r'[-+]?\$?[\d,]+(?:\.\d+)?/ton',w['text'])]
        if len(price_words) not in {3,5}:raise FormatError('Unknown monthly export price table column layout')
        price_words.sort(key=lambda w:w['x0']);centers=[(w['x0']+w['x1'])/2 for w in price_words]
        bounds=[centers[0]-(centers[1]-centers[0])/2]+[(a+b)/2 for a,b in zip(centers,centers[1:])]+[centers[-1]+(centers[-1]-centers[-2])/2]
        meta_text=page.crop((0,max(0,title['top']-1),page.width,change['bottom']+2)).extract_text(x_tolerance=1,y_tolerance=2)
        id=collector.table(title['text'],page_number,meta_text,'monthly-export-price-summary')
        month_match=re.match(r'(\w+)\s+(20\d{2})\s+(.+?) Export Prices',title['text'])
        if not month_match:raise FormatError('Missing monthly price period/commodity definition')
        period=datetime.strptime(month_match[1]+' '+month_match[2],'%B %Y').strftime('%Y-%m');commodity=month_match[3]
        for c,w in enumerate(price_words):
            quote=normalize(' '.join(x['text'] for x in words if title['bottom']<x['top']<average['top'] and bounds[c]<=(x['x0']+x['x1'])/2<bounds[c+1]))
            if not quote:raise FormatError('Missing monthly export price source/quote definition')
            value=w['text'].replace('$','').replace('/ton','')
            collector.add(id,section=commodity,row=quote,indicator='Monthly average export price',period=period,comparison='average',unit='U.S. Dollars per Metric Ton',value=value,page=page_number,line=c,commodity=commodity,basis='Source calendar-month average export quote, original location/FOB definition retained')
            tokens=[x['text'] for x in words if abs(x['top']-change['top'])<3 and bounds[c]<=(x['x0']+x['x1'])/2<bounds[c+1]]
            number=next((x for x in tokens if re.fullmatch(r'[-+]?\$?[\d,]+(?:\.\d+)?/ton',x)),None)
            if number is None:raise FormatError('Missing monthly price change value')
            sign='-' if any(x in {'-','−','‐','–'} for x in tokens) else ''
            collector.add(id,section=commodity,row=quote,indicator='Monthly export price change',period=period,comparison=change['text'].split('$',1)[0].rstrip('+- ').strip(),unit='U.S. Dollars per Metric Ton',value=sign+number.replace('$','').replace('/ton','').lstrip('+'),page=page_number,line=c,commodity=commodity,basis='Change against prior month explicitly printed in source row heading')


def parse_india_bangladesh_revisions(collector,page_number,page,text):
    title='Soybean Meal Trade Revisions for India and Bangladesh'
    lines=page.extract_text_lines(x_tolerance=1,y_tolerance=3,return_chars=False)
    header=next(l for l in lines if l['text'].startswith('Country Commodity Marketing Attribute'))
    words=[w for w in page.extract_words(x_tolerance=1,y_tolerance=2) if w['top']>header['bottom']]
    countries=[w for w in words if w['text'] in {'India','Bangladesh'}]
    attributes=[w for w in words if w['text'] in {'Imports','Exports'}]
    years=[w for w in words if re.fullmatch(r'20\d{2}/20\d{2}',w['text'])]
    if len(countries)!=2 or len(attributes)!=2 or len(years)!=6:raise FormatError('Unknown India/Bangladesh trade-revisions layout')
    id=collector.table(title,page_number,text,'source-specific-trade-revision-years')
    for i,year in enumerate(years):
        country=min(countries,key=lambda w:abs(w['top']-year['top']))
        attribute=min(attributes,key=lambda w:abs(w['top']-year['top']))
        values=sorted([w for w in words if w['x0']>year['x1'] and abs(w['top']-year['top'])<3 and NUM.fullmatch(w['text'])],key=lambda w:w['x0'])
        if len(values)!=3:raise FormatError('Missing numeric values in explicit trade revision row')
        for comparison,value in zip(['Previous','Current','Change'],values):collector.add(id,section=attribute['text'],row=country['text'],indicator=attribute['text'],period=year['text'],comparison=comparison,unit='Thousand Metric Tons',value=value['text'],page=page_number,line=i,commodity='Meal, Soybean',basis='Original source marketing-year labels; explicit India/Bangladesh trade-revision table')


def verify_grain_summary_unit(frame,evidence):
    """Verify omitted summary units against unit-labelled production in the same report."""
    summaries=[m for m in evidence['metadata'].values() if m['title']=='All Grain Summary Comparison' and 'Metric Tons' not in m['complete_source_text']]
    if not summaries:return []
    checks=[]
    for commodity,title in [('Wheat','World Wheat Production, Consumption, and Stocks'),('Rice, Milled','World Rice Production, Consumption, and Stocks'),('Corn','World Corn Production, Consumption, and Stocks')]:
        rows=frame[(frame.table_title=='All Grain Summary Comparison') & (frame.column_commodity==commodity) & (frame.indicator=='Production') & (frame.row_label=='World Total')]
        if len(rows)!=3:raise ValidationError('Cannot verify omitted grain summary unit against three source years')
        for row in rows.to_dict('records'):
            other=frame[(frame.table_title==title) & (frame.period_label==row['period_label']) & (frame.row_label=='World Total') & (frame.indicator.isin(['Production','Milled Production']))]
            if len(other)>1:other=other[other.comparison_label==MONTHS[int(row['report_period'][-2:])-1]]
            if len(other)!=1 or other.iloc[0]['unit']!='Thousand Metric Tons':raise ValidationError('Missing unit-labelled grain production comparison')
            expected=other.iloc[0]['value']/Decimal(1000)
            tolerance=Decimal('0.5')*Decimal(10)**row['value'].as_tuple().exponent
            if abs(row['value']-expected)>tolerance:raise ValidationError('Omitted summary unit fails same-report scale reconciliation')
            checks.append({'commodity':commodity,'period':row['period_label'],'summary_value':str(row['value']),'detailed_value_thousand_metric_tons':str(other.iloc[0]['value']),'tolerance_million_metric_tons':str(tolerance),'status':'pass'})
    return checks
