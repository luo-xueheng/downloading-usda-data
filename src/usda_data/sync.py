"""Persisted complete-run orchestration, revision checks and resumable publication."""
from datetime import datetime,timezone
from dataclasses import dataclass,asdict
from pathlib import Path
from uuid import uuid4
import json
import tomllib
import os
from .security import sanitize
from .config import DATASETS
from .errors import ConfigurationError,USDAError,ValidationError,PendingRelease
from .storage import atomic_write,canonical,sha256,hash_file,safe_name
from .sources.fas_common import refresh_operation

@dataclass(frozen=True)
class Task:
    task_id: str
    dataset: str
    options: dict
    required: bool = True

    def __post_init__(self):
        safe_name(self.task_id)
        if self.dataset not in DATASETS:raise ConfigurationError('Unknown task dataset')


def load_tasks(path,*,dataset='all'):
    path=Path(path)
    config=json.loads(path.read_text()) if path.suffix=='.json' else tomllib.loads(path.read_text())
    if set(config)-{'schema_version','data_dir','output_dir','refresh_policy','tasks','description','calendar','memory_budget_mib','scope_mode'}:
        raise ConfigurationError('Unknown sync configuration field')
    tasks=[]
    if not config.get('tasks'):raise ConfigurationError('Sync configuration must explicitly enumerate tasks/ranges; discovery/backfill planning creates them first')
    for raw in config['tasks']:
        if set(raw)-{'task_id','dataset','options','required'}:raise ConfigurationError('Unknown sync task field')
        task=Task(**raw)
        if dataset=='all' or task.dataset==dataset:tasks.append(task)
    if not tasks:raise ConfigurationError('No tasks selected')
    if len({t.task_id for t in tasks})!=len(tasks):raise ConfigurationError('Duplicate task IDs')
    # Refresh all configured partitions: no newest-only assumption for revisions.
    if config.get('refresh_policy','all_configured')!='all_configured':raise ConfigurationError('Only the verified all-configured-partitions refresh policy is supported')
    return config,tasks


def adapter_frames(task,data_dir,refresh):
    from .api import iter_wasde,iter_costs_returns,iter_export_sales,iter_rma_sob
    from .sources.report_datasets import iter_dataset
    from .sources import wasde,ers_costs_returns,fas_esr,rma_sob,report_datasets
    options=dict(task.options)
    import inspect
    functions={'wasde':(iter_wasde,wasde.SCHEMA),'costs-returns':(iter_costs_returns,ers_costs_returns.SCHEMA),'export-sales':(iter_export_sales,fas_esr.SCHEMA),'rma-sob':(iter_rma_sob,rma_sob.SCHEMA)}
    if task.dataset in functions:
        function,schema=functions[task.dataset]
        try:
            inspect.signature(function).bind(data_dir=data_dir,refresh=refresh,**options)
            frames=function(data_dir=data_dir,refresh=refresh,**options)
        except TypeError:raise ConfigurationError('Unsupported dataset task options') from None
    else:
        schema=report_datasets.SCHEMA
        try:
            inspect.signature(iter_dataset).bind(task.dataset,data_dir=data_dir,refresh=refresh,**options)
            frames=iter_dataset(task.dataset,data_dir=data_dir,refresh=refresh,**options)
        except TypeError:raise ConfigurationError('Unsupported report task options') from None
    return frames,schema


def production_runner(task,*,data_dir,output_dir,refresh):
    from .cli import export_frames
    frames,schema=adapter_frames(task,data_dir,refresh)
    return export_frames(frames,output_dir,dataset=task.dataset,schema=schema)


def execute(tasks,*,data_dir='data',output_dir='data/exports',resume=False,refresh=True,runner=production_runner,now=None,failure_hook=None):
    """Allow only one writer per data root; release the lock even after interruption."""
    import fcntl
    runs=Path(data_dir)/'manifests/runs';runs.mkdir(parents=True,exist_ok=True)
    with (runs/'.writer.lock').open('a+') as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValidationError('Another fetch/sync process is writing this data root; resume after it exits') from None
        try:
            return _execute(tasks,data_dir=data_dir,output_dir=output_dir,resume=resume,refresh=refresh,runner=runner,now=now,failure_hook=failure_hook)
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


def _execute(tasks,*,data_dir='data',output_dir='data/exports',resume=False,refresh=True,runner=production_runner,now=None,failure_hook=None):
    """Run required partitions and atomically select only a complete export manifest.

    Task exports are isolated per run. The global pointer remains on the previous
    complete run after any failure. Successful tasks survive resume; failed tasks
    have no advanced watermark. Every attempt is logged, including unchanged data.
    """
    now=now or (lambda:datetime.now(timezone.utc));data=Path(data_dir);output=Path(output_dir)
    serialized=[asdict(t) for t in tasks]
    if runner is production_runner:
        # Signature/range errors are user argument errors, not partial source runs.
        for task in tasks:
            adapter_frames(task,data_dir,refresh)
    if not tasks or len({t.task_id for t in tasks})!=len(tasks):raise ConfigurationError('Empty or duplicate run tasks')
    config_hash=sha256(canonical(serialized));runs=data/'manifests/runs';runs.mkdir(parents=True,exist_ok=True)
    active_path=runs/'active.json';old_complete_path=output/'complete.latest.json'
    old_complete=json.loads(old_complete_path.read_text()) if old_complete_path.exists() else None
    state=None
    if resume and active_path.exists():
        active=json.loads(active_path.read_text());candidate=json.loads((runs/(active['run_id']+'.json')).read_text())
        if candidate['configuration_hash']!=config_hash:raise ConfigurationError('Cannot resume with changed task inventory/options')
        if candidate['status'] in {'running','partial','failed'}:state=candidate
    if state is None:
        run_id=now().strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:8]
        state={'schema_version':1,'run_id':run_id,'configuration_hash':config_hash,'started_at_utc':now().isoformat(),'status':'running','tasks':{t.task_id:{'definition':asdict(t),'status':'pending','attempts':[],'watermark':None} for t in tasks},'artifact_availability':{},'refresh_policy':'all_configured_partitions'}
    run_id=state['run_id'];run_dir=output/'runs'/run_id
    def save():
        atomic_write(runs/(run_id+'.json'),canonical(state));atomic_write(active_path,canonical({'run_id':run_id,'configuration_hash':config_hash}))
    save()
    with refresh_operation():
        for task in tasks:
            record=state['tasks'][task.task_id]
            if resume and record['status']=='succeeded':
                selected=record['export'];csv_path=output/selected['csv_path']
                if csv_path.exists() and hash_file(csv_path)==selected['csv_sha256']:continue
                record['status']='pending';record['watermark']=None
            record.pop('controlled_error',None);record.pop('error_type',None)
            attempt={'started_at_utc':now().isoformat(),'status':'running'};record['attempts'].append(attempt);record['status']='running';save()
            task_output=run_dir/task.task_id
            try:
                if failure_hook:failure_hook('before_download',task)
                manifest=runner(task,data_dir=data,output_dir=task_output,refresh=refresh)
                csv_path=task_output/manifest['csv_path'];schema_path=task_output/manifest['schema_path']
                if not csv_path.exists() or hash_file(csv_path)!=manifest['csv_sha256'] or not schema_path.exists():raise ValidationError('Task runner returned incomplete or corrupt export')
                if failure_hook:failure_hook('after_normalization',task)
                selected={**manifest,'csv_path':str(csv_path.relative_to(output)),'schema_path':str(schema_path.relative_to(output))}
                record.update(status='succeeded',export=selected,watermark=now().isoformat())
                attempt.update(status='succeeded',completed_at_utc=now().isoformat(),csv_sha256=manifest['csv_sha256'])
                state['artifact_availability'][task.task_id]='available'
            except Exception as exc:
                # Do not persist arbitrary exception messages: upstream text can contain secrets.
                if isinstance(exc,USDAError):record['controlled_error']=sanitize(str(exc),[os.environ.get('USDA_FAS_API_KEY','')])
                record.update(status='pending_release' if isinstance(exc,PendingRelease) else 'failed',watermark=None,error_type=type(exc).__name__)
                attempt.update(status='failed',completed_at_utc=now().isoformat(),error_type=type(exc).__name__)
                state['artifact_availability'][task.task_id]='pending' if isinstance(exc,PendingRelease) else 'failed_or_unavailable'
            save()
    required_failures=[t.task_id for t in tasks if t.required and state['tasks'][t.task_id]['status']!='succeeded']
    if required_failures:
        state.update(status='partial',failed_required_tasks=required_failures,completed_at_utc=now().isoformat());save()
        return {'exit_code':1,'status':'partial','run_id':run_id,'state_path':str(runs/(run_id+'.json'))}
    exports={t.task_id:state['tasks'][t.task_id]['export'] for t in tasks if state['tasks'][t.task_id]['status']=='succeeded'}
    # Empty tasks are explicit complete responses, not implicit source-unavailability evidence.
    selection={'schema_version':1,'run_id':run_id,'configuration_hash':config_hash,'exports':exports,'completed_at_utc':now().isoformat(),'status':'complete'}
    try:
        if failure_hook:failure_hook('before_manifest_publication',None)
        manifest_path=run_dir/'complete.json';atomic_write(manifest_path,canonical(selection));atomic_write(old_complete_path,canonical(selection))
    except Exception as exc:
        state.update(status='partial',publication_error_type=type(exc).__name__,completed_at_utc=now().isoformat());save()
        return {'exit_code':1,'status':'partial','run_id':run_id,'state_path':str(runs/(run_id+'.json'))}
    unchanged=bool(old_complete) and {k:v['csv_sha256'] for k,v in old_complete['exports'].items()}=={k:v['csv_sha256'] for k,v in exports.items()}
    state.update(status='complete',completed_at_utc=now().isoformat(),unchanged=unchanged);save()
    return {'exit_code':0,'status':'unchanged' if unchanged else 'complete','run_id':run_id,'manifest_path':str(old_complete_path),'state_path':str(runs/(run_id+'.json'))}


def validate_export_root(path):
    """Verify exact hashes, explicit schemas and keys for selected complete exports."""
    from .schema import Schema
    import sqlite3,tempfile,os
    root=Path(path);manifest=root/'complete.latest.json'
    if manifest.exists():entries=list(json.loads(manifest.read_text())['exports'].values())
    else:entries=[json.loads(p.read_text()) for p in root.glob('*.latest.json')]
    if not entries:raise ValidationError('No selected export manifests')
    summaries=[]
    for entry in entries:
        csv_path=root/entry['csv_path'];schema=Schema.load(root/entry['schema_path'])
        if hash_file(csv_path)!=entry['csv_sha256']:raise ValidationError('Export hash mismatch')
        fd,pending=tempfile.mkstemp(suffix='.sqlite');os.close(fd);db=sqlite3.connect(pending);db.execute('CREATE TABLE keys (dimensions TEXT PRIMARY KEY)');count=0
        try:
            for frame in schema.read_csv_chunks(csv_path):
                keys=[(json.dumps([str(v.normalize()) if hasattr(v,'normalize') else str(v) for v in row]),) for row in frame[schema.keys].itertuples(index=False,name=None)]
                try:db.executemany('INSERT INTO keys VALUES (?)',keys)
                except sqlite3.IntegrityError:raise ValidationError('Duplicate business keys across exported partitions') from None
                count+=len(frame)
            if count!=entry['rows']:raise ValidationError('Export row-count mismatch')
        finally:db.close();Path(pending).unlink(missing_ok=True)
        summaries.append({'dataset':entry['dataset'],'rows':count,'sha256':entry['csv_sha256'],'status':'pass'})
    return summaries
