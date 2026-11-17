from datetime import datetime,timezone,date
from decimal import Decimal
from pathlib import Path
import json
import httpx
import pandas as pd
import pytest
from usda_data.sync import Task,execute,validate_export_root,load_tasks
from usda_data.storage import Store,atomic_write,canonical,sha256
from usda_data.schema import Field,Schema
from usda_data.cli import export_frames,main
from usda_data.calendar import PublicationEvent,calendar_status,presentation
from usda_data.errors import PendingRelease,DownloadError
from usda_data.http import HTTPClient
from usda_data.config import HTTPConfig

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'artifacts/acceptance/phase-08'
SCHEMA=Schema('synthetic_revision','1',(Field('code','string',False,'Synthetic business dimension','synthetic',key=True),Field('year','integer',False,'Synthetic observation year','synthetic',key=True),Field('value','decimal',True,'Synthetic signed exact amount','synthetic'),Field('source_artifact_id','string',False,'Source byte identity','synthetic raw'),Field('snapshot_id','string',False,'Version identity','storage')))
VERSIONS={'A':[{'code':'001','year':2024,'value':'10.00'},{'code':'002','year':2024,'value':'20.00'}],'B':[{'code':'001','year':2024,'value':'-3.25'},{'code':'003','year':2024,'value':'0.00'}]}


class Source:
    """Explicitly synthetic source versions; no official accuracy claim."""
    def __init__(self):self.versions={};self.calls=[];self.fail=set();self.pending=set()
    def __call__(self,task,*,data_dir,output_dir,refresh):
        self.calls.append((task.task_id,refresh))
        if task.task_id in self.fail:raise OSError('Synthetic interrupted download')
        if task.task_id in self.pending:raise PendingRelease('Synthetic report pending')
        records=VERSIONS[self.versions.get(task.task_id,'A')];body=canonical(records);store=Store(data_dir)
        receipt=store.raw(body,metadata={'url':'https://synthetic.test/unchanged-source-url'})
        frame=SCHEMA.frame([{**r,'value':Decimal(r['value']),'source_artifact_id':receipt['source_artifact_id'],'snapshot_id':'unpublished'} for r in records])
        snapshot=store.publish(task.dataset,task.task_id,frame,SCHEMA,[receipt['source_artifact_id']],parser_version='synthetic-1',configuration={})
        return export_frames([SCHEMA.read_csv(store.root/snapshot['csv_path'])],output_dir,dataset=task.dataset,schema=SCHEMA)


def latest(output):return json.loads((output/'complete.latest.json').read_text())
def business(output,manifest,task):
    frame=SCHEMA.read_csv(output/manifest['exports'][task]['csv_path'])
    return frame[['code','year','value']].to_dict('records')


@pytest.mark.acceptance('P08-A1')
def test_revision_B_replaces_added_changed_removed_rows(tmp_path):
    source=Source();tasks=[Task('p2024','wasde',{})];data=tmp_path/'data';output=tmp_path/'exports'
    first=execute(tasks,data_dir=data,output_dir=output,runner=source);a=latest(output)
    source.versions['p2024']='B';second=execute(tasks,data_dir=data,output_dir=output,runner=source);b=latest(output)
    assert first['exit_code']==second['exit_code']==0
    assert business(output,b,'p2024')==[{**r,'value':Decimal(r['value'])} for r in VERSIONS['B']]
    assert business(output,a,'p2024')==[{**r,'value':Decimal(r['value'])} for r in VERSIONS['A']]
    assert len(list((data/'normalized/wasde/p2024').iterdir()))==2


@pytest.mark.acceptance('P08-A2')
def test_earlier_year_revision_same_url_is_checked(tmp_path):
    source=Source();tasks=[Task('old2024','wasde',{}),Task('recent2025','wasde',{})];data=tmp_path/'data';out=tmp_path/'out'
    execute(tasks,data_dir=data,output_dir=out,runner=source);before=latest(out)
    source.versions['old2024']='B';source.calls=[]
    execute(tasks,data_dir=data,output_dir=out,runner=source);after=latest(out)
    assert source.calls==[('old2024',True),('recent2025',True)]
    assert before['exports']['old2024']['csv_sha256']!=after['exports']['old2024']['csv_sha256']
    assert before['exports']['recent2025']['csv_sha256']==after['exports']['recent2025']['csv_sha256']


@pytest.mark.acceptance('P08-A3')
def test_unchanged_checks_are_logged_without_new_snapshots(tmp_path):
    source=Source();tasks=[Task('p','wasde',{})];data=tmp_path/'data';out=tmp_path/'out'
    a=execute(tasks,data_dir=data,output_dir=out,runner=source);b=execute(tasks,data_dir=data,output_dir=out,runner=source)
    assert a['run_id']!=b['run_id'] and b['status']=='unchanged'
    assert len(list((data/'normalized/wasde/p').iterdir()))==1
    assert len(source.calls)==2
    assert json.loads(Path(b['state_path']).read_text())['tasks']['p']['attempts'][0]['status']=='succeeded'
    assert validate_export_root(out)[0]['rows']==2


@pytest.mark.acceptance('P08-A4')
@pytest.mark.parametrize('stage',['before_download','after_normalization','before_manifest_publication'])
def test_failure_and_resume_never_select_partial_output(tmp_path,stage):
    source=Source();tasks=[Task('p','wasde',{})];data=tmp_path/'data';out=tmp_path/'out'
    execute(tasks,data_dir=data,output_dir=out,runner=source);previous=(out/'complete.latest.json').read_bytes()
    source.versions['p']='B'
    def fail(at,task):
        if at==stage:raise OSError('Synthetic crash at '+stage)
    result=execute(tasks,data_dir=data,output_dir=out,runner=source,failure_hook=fail)
    assert result['exit_code']==1 and (out/'complete.latest.json').read_bytes()==previous
    state=json.loads(Path(result['state_path']).read_text())
    if stage!='before_manifest_publication':assert state['tasks']['p']['watermark'] is None
    resumed=execute(tasks,data_dir=data,output_dir=out,runner=source,resume=True)
    assert resumed['exit_code']==0
    assert business(out,latest(out),'p')==[{**r,'value':Decimal(r['value'])} for r in VERSIONS['B']]


@pytest.mark.acceptance('P08-A5')
def test_partial_required_job_and_resume_equals_clean_run(tmp_path):
    tasks=[Task('first','wasde',{}),Task('second','costs-returns',{})];source=Source();data=tmp_path/'data';out=tmp_path/'out'
    execute(tasks,data_dir=data,output_dir=out,runner=source);old=(out/'complete.latest.json').read_bytes()
    source.versions={'first':'B','second':'B'};source.fail={'second'}
    failed=execute(tasks,data_dir=data,output_dir=out,runner=source)
    assert failed['exit_code']==1 and (out/'complete.latest.json').read_bytes()==old
    state=json.loads(Path(failed['state_path']).read_text());assert state['tasks']['first']['status']=='succeeded' and state['tasks']['second']['watermark'] is None
    source.fail=set();source.calls=[]
    success=execute(tasks,data_dir=data,output_dir=out,runner=source,resume=True);assert success['exit_code']==0
    assert source.calls==[('second',True)]
    clean=tmp_path/'clean';clean_source=Source();clean_source.versions={'first':'B','second':'B'}
    execute(tasks,data_dir=clean/'data',output_dir=clean/'out',runner=clean_source)
    assert {k:v['csv_sha256'] for k,v in latest(out)['exports'].items()}=={k:v['csv_sha256'] for k,v in latest(clean/'out')['exports'].items()}


@pytest.mark.acceptance('P08-A6')
def test_timezones_and_date_only_precision():
    for day,expected in [('2026-01-15','2026-01-15T17:00:00+00:00'),('2026-07-15','2026-07-15T16:00:00+00:00')]:
        e=PublicationEvent('wasde','report',day,'https://synthetic.test/timezone','2026-01-01T00:00:00+00:00','12:00:00','America/New_York')
        assert e.utc().isoformat()==expected
        assert presentation(e)['display_release_at'].endswith('+08:00')
    date_only=PublicationEvent('costs-returns','file','2026-07-15','https://synthetic.test/date','2026-07-01T00:00:00+00:00')
    assert date_only.utc() is None and presentation(date_only)['display_release_at'] is None


@pytest.mark.acceptance('P08-A7')
def test_saved_shifted_event_delay_and_staleness():
    event=PublicationEvent('export-sales','weekly_release','2026-11-13','https://synthetic.test/holiday','2026-11-10T00:00:00+00:00','08:30:00','America/New_York')
    # Explicit synthetic holiday shift to Friday, not a hard-coded Thursday rule.
    assert calendar_status(event,datetime(2026,11,12,15,tzinfo=timezone.utc))=='pending'
    assert calendar_status(event,datetime(2026,11,13,15,tzinfo=timezone.utc))=='delayed'
    assert calendar_status(event,datetime(2026,12,31,tzinfo=timezone.utc))=='stale_calendar'
    assert calendar_status(event,datetime(2026,11,13,15,tzinfo=timezone.utc),available=True)=='available'


@pytest.mark.acceptance('P08-A8')
def test_api_available_while_report_pending(tmp_path):
    tasks=[Task('api','export-sales',{}),Task('report','world-production',{})];source=Source();source.pending={'report'}
    result=execute(tasks,data_dir=tmp_path/'data',output_dir=tmp_path/'out',runner=source)
    assert result['status']=='partial'
    state=json.loads(Path(result['state_path']).read_text())
    assert state['artifact_availability']=={'api':'available','report':'pending'}
    assert state['tasks']['report']['watermark'] is None
    assert not (tmp_path/'out/complete.latest.json').exists()


@pytest.mark.acceptance('P08-A3')
def test_configured_dry_run_has_no_numeric_downloads(capsys):
    assert main(['fetch','--dataset','all','--config',str(ROOT/'config/small_sync.json'),'--dry-run'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['numeric_downloads'] is False and result['task_count']==7


@pytest.mark.live
@pytest.mark.acceptance('P08-A9')
def test_real_bounded_revision_check_and_finite_unavailable_failure(tmp_path):
    from usda_data.sources import fas_esr
    from usda_data.sources import fas_common
    from usda_data.sync import production_runner
    store=Store(OUT/'live/data');dest=OUT/'live/exports'
    tasks=[Task('corn2026','export-sales',{'commodities':['401'],'market_years':[2026],'countries':['1220']})]
    first=execute(tasks,data_dir=store.root,output_dir=dest,refresh=True)
    assert first['exit_code']==0
    second=execute(tasks,data_dir=store.root,output_dir=dest,refresh=True)
    assert second['exit_code']==0 and second['status']=='unchanged'
    assert validate_export_root(dest)[0]['rows']>0
    calls=[]
    def handler(request):calls.append(request);return httpx.Response(503)
    with HTTPClient(HTTPConfig(max_attempts=2),transport=httpx.MockTransport(handler),sleep=lambda _:None) as client:
        with pytest.raises(DownloadError):client.get('https://synthetic.test/unavailable',expected='json')
    assert len(calls)==2
    atomic_write(OUT/'live/checks.json',canonical({'first_run':first,'unchanged_run':second,'finite_unavailable_attempts':len(calls),'status':'pass'}))
