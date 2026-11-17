"""WASDE official long-form historical and current monthly CSV adapter.

The current monthly CSV is the selected current-release structured format.
XML supplies separately retained report footnotes and cross-format checks; it
never silently overwrites the official historical observation series.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import csv
import io
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, InvalidOperation
import pandas as pd
from ..errors import ConfigurationError, FormatError, ValidationError, AuthenticationError, DownloadError
from ..http import HTTPClient
from ..schema import Field, Schema
from ..storage import Store, atomic_write, canonical, sha256, utc_now

PARSER_VERSION = "wasde-csv-3"
REPAIRS = json.loads(Path(__file__).with_name("wasde_dimension_repairs.json").read_text())
LANDING = "https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report"
HISTORY = LANDING + "/historical-wasde-report-data"
COLUMNS = ["WasdeNumber","ReportDate","ReportTitle","Attribute","ReliabilityProjection","Commodity","Region","MarketYear","ProjEstFlag","AnnualQuarterFlag","Value","Unit","ReleaseDate","ReleaseTime","ForecastYear","ForecastMonth"]
DIMENSIONS = ["WasdeNumber","ReportTitle","Attribute","ReliabilityProjection","Commodity","Region","MarketYear","ProjEstFlag","AnnualQuarterFlag","Unit","ForecastYear","ForecastMonth"]
OPTIONAL = {"ReliabilityProjection":"not_applicable", "MarketYear":"not_applicable", "ProjEstFlag":"not_labelled"}
MISSING = {"":"missing", "NA":"unavailable", "N/A":"not_applicable", "(D)":"suppressed", "(S)":"suppressed", "--":"unavailable"}

def schema():
    fields=[]
    for column in COLUMNS:
        if column == "Value":
            fields.append(Field(column,"decimal",True,"Exact reported numeric value; source markers remain in raw_value","Value","Unit column"))
        else:
            fields.append(Field(column,"string",False,"Original source label; explicit sentinels only for documented empty optional dimensions",column,key=column in DIMENSIONS))
    fields += [Field("source_release_date","date",False,"Report publication date, inclusive request filter","ReleaseDate",key=True),Field("source_release_at_utc","datetime",True,"Exact publication instant only when timezone independently verified","not inferred from time-only CSV"),Field("release_time_precision","string",False,"Precision of confirmed UTC publication information","date"),Field("retrieved_at_utc","datetime",False,"First receipt time for this snapshot","acquisition manifest"),Field("source_artifact_id","string",False,"SHA-256 of original file or ZIP bytes","raw storage"),Field("snapshot_id","string",False,"Version-aware normalized identity","storage manifest"),Field("vintage_type","string",False,"Report-vintage rather than current-revised API series","WASDE report date"),Field("raw_value","string",False,"Exact original numeric lexical value or marker","Value"),Field("value_status","string",False,"reported/missing/suppressed/unavailable/not_applicable","Value marker"),Field("raw_optional_dimensions","string",False,"Original empty/label values for optional classifications","ReliabilityProjection,MarketYear,ProjEstFlag"),Field("source_member","string",False,"ZIP member or empty string for standalone CSV","ZIP inventory")]
    fields += [Field("source_dimension_repair","string",False,"Evidence ID for an exact-source dimension repair; empty if none","versioned repair registry"), Field("source_original_dimensions","string",False,"Original dimension values before an independently evidenced repair","original CSV record"), Field("source_conflict","string",False,"Known cross-format numeric discrepancy; CSV value retained","versioned repair registry")]
    return Schema("wasde_observations","2",tuple(fields))

SCHEMA = schema()

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(v for k,v in attrs if k=="href" and v)

def official(url):
    parsed=urlsplit(url)
    return parsed.scheme=="https" and (parsed.hostname=="usda.gov" or (parsed.hostname or "").endswith(".usda.gov") or parsed.hostname=="usda.azureedge.us")

def discover(client, store):
    """Read official current/history pages; retain evidence and all candidate links."""
    result=[]
    for url, kind in [(LANDING,"current"),(HISTORY,"history")]:
        try:
            body,metadata=client.get(url,expected="html")
        except (AuthenticationError, DownloadError):
            if kind != "history":
                raise
            body,metadata=client.get("https://usda.azureedge.us/historical-wasde-report-data-3",expected="html")
            metadata["original_url"] = url
            metadata["original_access_status"] = "unavailable_after_bounded_attempts"
        receipt=store.raw(body,metadata=metadata)
        parser=Links();parser.feed(body.decode("utf-8"))
        base=metadata["url"]
        for link in parser.links:
            target=urljoin(base,link)
            if not official(target):
                continue
            if re.search(r"oce-wasde-report-data-.*\.(csv|zip)$",target,re.I) or re.search(r"wasde\d{4}\.xml$",target,re.I):
                result.append({"url":target,"format":target.rsplit(".",1)[-1].lower(),"discovery_artifact_id":receipt["source_artifact_id"],"kind":kind})
    unique={x["url"]:x for x in result}
    if not any(x["format"]=="csv" for x in unique.values()) or not any(x["format"]=="xml" for x in unique.values()):
        raise FormatError("WASDE discovery lacks expected structured formats")
    manifest={"checked_at_utc":utc_now(),"links":list(unique.values()),"earliest_structured_archive":"2010-04","earlier_history":"Earlier layouts are not supported; no January 2010 structured coverage is claimed"}
    atomic_write(store.root/"manifests/wasde/discovery.json",canonical(manifest))
    return manifest

@contextmanager
def source_members(path):
    """Open one CSV member at a time; compressed archives have bounded members."""
    path=Path(path)
    with path.open("rb") as stream:
        signature=stream.read(4)
    if signature.startswith(b"PK"):
        archive=zipfile.ZipFile(path)
        infos=archive.infolist()
        if not infos or any(i.filename.startswith("/") or ".." in Path(i.filename).parts or not i.filename.lower().endswith(".csv") or i.file_size>250_000_000 for i in infos):
            archive.close();raise FormatError("Unknown or unsafe WASDE ZIP member")
        try:
            yield ((i.filename,io.TextIOWrapper(archive.open(i),encoding="utf-8-sig",newline="")) for i in infos)
        finally:
            archive.close()
    else:
        with path.open(encoding="utf-8-sig",newline="") as stream:
            yield iter([("",stream)])

def source_date(value):
    """Verified historical layouts use ISO or US month/day/year release dates."""
    try:return date.fromisoformat(value)
    except ValueError:
        try:return datetime.strptime(value,'%m/%d/%Y').date()
        except ValueError:raise FormatError('Unknown WASDE source release-date representation') from None


def normalize(row, receipt, member):
    if set(row)!=set(COLUMNS) or None in row.values():
        raise FormatError("Unexpected WASDE field layout or row width")
    original_dimensions = {}
    repair_id = ""
    conflict = ""
    if receipt["source_artifact_id"] == REPAIRS["archive_sha256"]:
        for repair in REPAIRS["entries"]:
            if row == repair["match"]:
                original_dimensions = {k: row[k] for k in repair["replace"]}
                row = {**row, **repair["replace"]}
                repair_id = REPAIRS["id"]
                if row["ReliabilityProjection"] == REPAIRS["numeric_conflict"]["metric"]:
                    conflict = json.dumps(REPAIRS["numeric_conflict"], sort_keys=True)
                break
    for correction in REPAIRS.get('additional_exact_artifact_repairs',[]):
        if receipt['source_artifact_id']==correction['archive_sha256']:
            for repair in correction['entries']:
                if row==repair['match']:
                    original_dimensions={k:row[k] for k in repair['replace']}
                    row={**row,**repair['replace']};repair_id=correction['id'];break
    try:
        release=source_date(row["ReleaseDate"])
        if (release.year,release.month)!=(int(row["ForecastYear"]),int(row["ForecastMonth"])):
            raise ValueError()
        if datetime.strptime(row["ReportDate"],"%B %Y").date().replace(day=1)!=release.replace(day=1):
            raise ValueError()
    except (TypeError,ValueError):
        raise FormatError("Inconsistent WASDE report date labels") from None
    for column in DIMENSIONS:
        if not row[column] and column not in OPTIONAL:
            raise ValidationError(f"Source omits required WASDE dimension: {column}; release {release}")
    if not row['MarketYear'] and not row['ReportTitle'].startswith('Reliability of '):
        raise ValidationError("Missing source period outside reliability statistics")
    raw=row["Value"]
    if raw in MISSING:
        value=None;value_status=MISSING[raw]
    else:
        try:
            value=Decimal(raw)
            if not value.is_finite():
                raise InvalidOperation()
        except InvalidOperation:
            raise FormatError("Unknown WASDE numeric value/marker") from None
        value_status="reported"
    output=dict(row)
    output.update({k:row[k] or sentinel for k,sentinel in OPTIONAL.items()})
    output.update(source_dimension_repair=repair_id,source_original_dimensions=json.dumps(original_dimensions,sort_keys=True),source_conflict=conflict,Value=value,source_release_date=release,source_release_at_utc=None,release_time_precision="date",retrieved_at_utc=datetime.fromisoformat(receipt["retrieved_at_utc"]),source_artifact_id=receipt["source_artifact_id"],snapshot_id="unpublished",vintage_type="report_vintage",raw_value=raw,value_status=value_status,raw_optional_dimensions=json.dumps({k:row[k] for k in OPTIONAL},sort_keys=True),source_member=member)
    return output

def bounds(start,end):
    try:
        start=date.fromisoformat(str(start));end=date.fromisoformat(str(end))
    except ValueError:
        raise ConfigurationError("WASDE bounds must be ISO publication dates YYYY-MM-DD") from None
    if start>end:
        raise ConfigurationError("WASDE start must not follow end")
    return start,end

def iter_csv_partitions(path, receipt, *, start, end, accounting=None):
    """Yield report-vintage partitions with at most one report in memory.

    Rows outside inclusive bounds are explicitly counted. In-scope missing
    dimensions, repeated noncontiguous partitions or changed layouts fail.
    """
    start,end=bounds(start,end)
    accounting=accounting if accounting is not None else {}
    accounting.update(input_rows=0,mapped_rows=0,excluded_outside_bounds=0,quarantined_rows=0,tables={})
    seen=set();current=None;records=[]
    with source_members(path) as members:
        for member,stream in members:
            try:
                reader=csv.DictReader(stream)
                if reader.fieldnames!=COLUMNS:
                    raise FormatError("Unauthorized WASDE CSV layout change")
                for row in reader:
                    accounting['input_rows']+=1
                    if set(row)!=set(COLUMNS) or None in row.values():
                        accounting['quarantined_rows']+=1
                        raise FormatError("Unexpected WASDE row width")
                    try:
                        release=source_date(row['ReleaseDate'])
                    except ValueError:
                        raise FormatError("Invalid source release date") from None
                    if not start<=release<=end:
                        accounting['excluded_outside_bounds']+=1;continue
                    if current!=release:
                        if records:
                            yield current,SCHEMA.frame(records)
                        if release in seen:
                            raise FormatError("Noncontiguous duplicate report partition")
                        seen.add(release);current=release;records=[]
                    try:
                        records.append(normalize(row,receipt,member))
                    except (FormatError,ValidationError):
                        accounting['quarantined_rows']+=1;raise
                    accounting['mapped_rows']+=1
                    title=row['ReportTitle'];accounting['tables'][title]=accounting['tables'].get(title,0)+1
            finally:
                stream.close()
    if records:
        yield current,SCHEMA.frame(records)
    if accounting['input_rows'] != accounting['mapped_rows']+accounting['excluded_outside_bounds']+accounting['quarantined_rows']:
        raise ValidationError("WASDE parser accounting mismatch")

def relevant(link,start,end):
    """Candidate month bounds select files; rows still use exact release dates."""
    name=link['url'].rsplit('/',1)[-1]
    months=re.findall(r'(20\d{2})-(\d{2})',name)
    if not months:
        return False
    lower=date(int(months[0][0]),int(months[0][1]),1)
    upper=date(int(months[-1][0]),int(months[-1][1]),1)
    return lower<=end.replace(day=1) and upper>=start.replace(day=1)

def xml_footnotes(body):
    root=ET.fromstring(body)
    if root.tag!='Report' or root.attrib.get('Name')!='wasde':
        raise FormatError("Unexpected WASDE XML layout")
    result=[]
    for table in root:
        report=table.find('Report')
        if report is None:
            raise FormatError("Unknown XML report container")
        result.append({'source_table':table.tag,'report_month':report.get('Report_Month'),'titles':{k:v for k,v in report.attrib.items() if k.startswith('sub_report_title')},'footnotes':[{"element":node.tag,"field":k,"text":v} for node in report.iter() for k,v in node.attrib.items() if 'footer' in k]})
    return result

def iter_download(start,end,*,data_dir='data',refresh=False,client=None):
    """Download/cache source files and yield validated report partitions.

    Raw bytes and receipts survive revisions. refresh refetches discovery and
    candidates; complete report snapshots are published atomically. This iterator
    is the bounded-memory interface used by CLI jobs.
    """
    start,end=bounds(start,end);store=Store(data_dir)
    owned=client is None;client=client or HTTPClient()
    try:
        discovery_path=store.root/'manifests/wasde/discovery.json'
        discovery=discover(client,store) if refresh or not discovery_path.exists() else json.loads(discovery_path.read_text())
        links=[l for l in discovery['links'] if l['format'] in {'csv','zip'} and relevant(l,start,end)]
        if not links:
            raise ValidationError("No discovered structured WASDE file covers requested dates")
        selected_dates=set()
        for link in sorted(links,key=lambda l:l['url']):
            cache_path=store.root/'manifests/wasde/urls'/f"{sha256(link['url'].encode())}.json"
            if cache_path.exists() and not refresh:
                receipt=json.loads(cache_path.read_text());path=store.artifact(receipt['source_artifact_id'])
            else:
                try:
                    body,metadata=client.get(link['url'],expected=link['format'])
                except AuthenticationError:
                    if link['format']!='zip' or not link['url'].startswith('https://www.usda.gov/sites/default/files/documents/oce-wasde-report-data-'):
                        raise
                    alternate=link['url'].replace('https://www.usda.gov/','https://usda.azureedge.us/',1)
                    body,metadata=client.get(alternate,expected='zip')
                    metadata['original_url']=link['url']
                    metadata['original_access_status']=403
                receipt=store.raw(body,metadata=metadata)
                if cache_path.exists():
                    previous=json.loads(cache_path.read_text())
                    if previous['source_artifact_id']==receipt['source_artifact_id']:
                        receipt=previous
                atomic_write(cache_path,canonical(receipt));path=store.artifact(receipt['source_artifact_id'])
            accounting={}
            try:
                for release,frame in iter_csv_partitions(path,receipt,start=start,end=end,accounting=accounting):
                    if release in selected_dates:
                        raise ValidationError("Overlapping CSV sources require explicit reconciliation before publication")
                    selected_dates.add(release)
                    artifact_ids=[receipt['source_artifact_id']]
                    xml_links=[x for x in discovery['links'] if x['format']=='xml' and x['url'].endswith(release.strftime('wasde%m%y.xml'))]
                    if xml_links:
                        if len(xml_links)!=1:
                            raise FormatError('Ambiguous current XML artifact')
                        xml_url=xml_links[0]['url']
                        xml_cache=store.root/'manifests/wasde/urls'/f'{sha256(xml_url.encode())}.json'
                        if xml_cache.exists() and not refresh:
                            xml_receipt=json.loads(xml_cache.read_text());xml_body=store.artifact(xml_receipt['source_artifact_id']).read_bytes()
                        else:
                            xml_body,xml_meta=client.get(xml_url,expected='xml')
                            xml_receipt=store.raw(xml_body,metadata=xml_meta);atomic_write(xml_cache,canonical(xml_receipt))
                        artifact_ids.append(xml_receipt['source_artifact_id'])
                        comparisons,xml_accounting=reconcile_xml(frame,xml_body)
                        evidence={'release_date':release.isoformat(),'xml_artifact_id':xml_receipt['source_artifact_id'],'csv_artifact_id':receipt['source_artifact_id'],'comparisons':comparisons,'accounting':xml_accounting,'report_tables_and_footnotes':xml_footnotes(xml_body)}
                        atomic_write(store.root/'manifests/wasde/reconciliation'/f'{release}-{receipt["source_artifact_id"]}-{xml_receipt["source_artifact_id"]}.json',canonical(evidence))
                        if not comparisons or any(c['status']!='pass' for c in comparisons):
                            raise ValidationError('XML/CSV source conflict; raw evidence retained and publication blocked')
                    manifest=store.publish('wasde',release.isoformat(),frame,SCHEMA,artifact_ids,parser_version=PARSER_VERSION,configuration={'source':'official long-form CSV','layout':COLUMNS})
                    yield SCHEMA.read_csv(store.root/manifest['csv_path'])
            finally:
                atomic_write(store.root/'manifests/wasde/accounting'/f"{receipt['source_artifact_id']}-{start}-{end}.json",canonical(accounting))
        if not selected_dates:
            # A valid empty date interval is distinct from source/auth failure.
            yield SCHEMA.frame([])
    finally:
        if owned:
            client.close()


def clean_label(value):
    """Only whitespace, displayed footnote markers and explicit estimate flags."""
    value=re.sub(r'\d+/', '', value)
    value=re.sub(r'\(?\b(?:Est|Proj)\.\)?','',value)
    return ' '.join(value.split()).strip()


def parse_xml_summary(body):
    """Parse the three cross-format summary table families without using CSV values.

    This is a reconciliation reader, not an assertion of complete XML support.
    Full business-table coverage is supplied by the official monthly CSV format.
    Prior-month comparison columns remain in the XML archive and are explicitly
    excluded from the current forecast comparison, not relabelled as current.
    """
    root=ET.fromstring(body)
    rows=[];prior=0
    for tag in ['sr08','sr09','sr10']:
        report=root.find(f'{tag}/Report')
        if report is None:
            raise FormatError('Unsupported XML summary layout')
        report_month=report.get('Report_Month')
        current_month=datetime.strptime(report_month,'%B %Y').strftime('%b')
        for matrix in report:
            if not matrix.tag.startswith('matrix'):
                raise FormatError('Unexpected summary matrix')
            cotton=tag=='sr09' and matrix.tag=='matrix2'
            title='World and U.S. Supply and Use for '+('Cotton' if cotton else 'Oilseeds' if tag=='sr10' else 'Grains')
            unit='Million 480-lb Bales' if cotton else 'Million Metric Tons'
            def visit(node,context):
                nonlocal prior
                context=dict(context)
                for key,value in node.attrib.items():
                    stem=re.sub(r'\d+$','',key)
                    if stem in {'commodity','region','market_year','forecast_month','attribute','commodity_header'}:
                        context[stem]=value
                if node.tag=='Cell':
                    values=[v for k,v in node.attrib.items() if re.fullmatch(r'cell_value\d+',k)]
                    if len(values)>1:
                        raise FormatError('Multiple XML numeric values in one summary cell')
                    if values:
                        month=context.get('forecast_month','').strip()
                        if month and month!=current_month:
                            prior+=1;return
                        key={'ReportTitle':title,'Commodity':'Cotton' if cotton else clean_label(context['commodity']),'Region':clean_label(context.get('region',context.get('commodity_header',''))),'MarketYear':context['market_year'].split()[0],'Attribute':clean_label(context['attribute']),'Unit':unit}
                        raw=values[0].replace(',','')
                        rows.append({**key,'Value':None if raw in MISSING else Decimal(raw),'report_month':report_month,'forecast_column':month,'source_table':tag})
                for child in node:
                    visit(child,context)
            visit(matrix,{})
    return rows,{'mapped_current_summary_cells':len(rows),'excluded_prior_forecast_comparison_cells':prior,'other_xml_tables':'Not inputs to the summary reconciliation reader; every table family is independently covered by the official monthly CSV parser.'}


def reconcile_xml(frame,body):
    rows,accounting=parse_xml_summary(body)
    keys=['ReportTitle','Commodity','Region','MarketYear','Attribute','Unit']
    # CSV unit punctuation is source lexical metadata, not a scale conversion.
    def key_of(row):
        return tuple(row[k].replace('480-lb.','480-lb') if k=='Unit' else row[k] for k in keys)
    lookup={key_of(r):r for r in frame.to_dict('records')}
    comparisons=[]
    for row in rows:
        current=lookup.get(key_of(row))
        if current is None:
            comparisons.append({'dimensions':{k:row[k] for k in keys},'status':'missing_csv','xml_value':str(row['Value'])});continue
        comparisons.append({'dimensions':{k:row[k] for k in keys},'status':'pass' if current['Value']==row['Value'] and current['ReportDate']==row['report_month'] else 'conflict','xml_value':str(row['Value']),'csv_value':str(current['Value']),'tolerance':'0'})
    return comparisons,accounting
