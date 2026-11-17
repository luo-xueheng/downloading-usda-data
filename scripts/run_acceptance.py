#!/usr/bin/env python3
"""Record phase-specific pytest evidence; absent/skipped IDs never pass a gate."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {'01':7,'02':7,'03':7,'04':7,'05':8,'06':6,'07':7,'08':9,'09':7,'10':7}

class Recorder:
    def __init__(self):
        self.nodes = {}
        self.reports = {}

    def pytest_collection_modifyitems(self, items):
        for item in items:
            marker = item.get_closest_marker('acceptance')
            if marker:
                self.nodes[item.nodeid] = {'test_id':marker.args[0], 'mode':'live' if item.get_closest_marker('live') else 'offline'}

    def pytest_runtest_logreport(self, report):
        if report.nodeid in self.nodes:
            self.reports.setdefault(report.nodeid,[]).append({'when':report.when, 'outcome':report.outcome})

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def version():
    paths=[]
    for pattern in ['src/**/*.py','src/**/*.json','tests/**/*.py','tests/**/*.json','schemas/*.json','config/*','scripts/*.py','pyproject.toml']:
        paths.extend(ROOT.glob(pattern))
    hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(paths)) if p.is_file()}
    tree=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    git=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    return {'git_revision':git.stdout.strip() or None,'source_tree_sha256':tree,'file_hashes':hashes}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',required=True,choices=COUNTS)
    parser.add_argument('--mode',choices=['offline','live'],default='offline')
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    os.chdir(ROOT)
    output=ROOT/'artifacts/acceptance'/f'phase-{args.phase}'
    output.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).isoformat()
    code=version()
    configuration_hash=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'config').glob('*')) if p.is_file())).hexdigest()
    def record_command(argv, result):
        with (output/'commands.txt').open('a') as f:
            f.write(f'UTC: {stamp}\nWorking directory: {ROOT}\nCommand: {shlex.join(argv)}\nExit code: {result}\n\n')
    install_ok=True
    if args.install:
        command=[sys.executable,'-m','pip','install','--no-build-isolation','-e','.[dev]']
        result=subprocess.run(command,capture_output=True,text=True)
        (output/'installation.txt').write_text(result.stdout+result.stderr)
        record_command(command,result.returncode)
        install_ok=result.returncode==0
    capture=io.StringIO()
    recorder=Recorder()
    test_args=[f'tests/phase_{args.phase}','-m','not live' if args.mode=='offline' else 'live','-q']
    with redirect_stdout(capture),redirect_stderr(capture):
        result=pytest.main(test_args,plugins=[recorder])
    record_command([sys.executable,'-m','pytest',*test_args],int(result))
    (output/f'pytest.{args.mode}.txt').write_text(capture.getvalue())
    (output/f'test_cases.{args.mode}.json').write_text(json.dumps({'collected':recorder.nodes,'reports':recorder.reports,'exit_code':int(result)},indent=2)+'\n')
    (output/'code_version.json').write_text(json.dumps(code,indent=2)+'\n')
    environment={'python':sys.version,'executable':sys.executable,'packages':{name:importlib.metadata.version(name) for name in ['usda-data','pandas','httpx','pytest','setuptools']},'installation':'Acceptance runner environment; Phase 10 clean wheel installation is independently recorded in clean_environment.json and clean-install.command.json'}
    (output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    plan=(ROOT/'USDA_DATA_PHASED_EXECUTION_PLAN_EN.md').read_text()
    expected={line.split('|')[1].strip():line.split('|')[2].strip() for line in plan.splitlines() if line.startswith(f'| P{args.phase}-A')}
    rows=[]
    for test_id in sorted(expected):
        nodes=[node for node,meta in recorder.nodes.items() if meta['test_id']==test_id and meta['mode']==args.mode]
        reports=[r for node in nodes for r in recorder.reports.get(node,[])]
        passes=result==0 and bool(nodes) and all(any(r['when']=='call' and r['outcome']=='passed' for r in recorder.reports.get(n,[])) for n in nodes) and all(r['outcome']=='passed' for r in reports)
        if test_id=='P01-A1':
            passes=passes and install_ok and (output/'installation.txt').exists()
        status='pass' if passes else 'fail' if any(r['outcome']=='failed' for r in reports) else 'blocked'
        rows.append({'phase_id':args.phase,'test_id':test_id,'mode':args.mode,'status':status,'observed_result':f'{len(nodes)} selected tests; '+('; '.join(f"{n}: {recorder.reports.get(n,[])}" for n in nodes) or 'No test executed'),'expected_result':expected[test_id],'evidence_path':str(output.relative_to(ROOT)), 'code_version':{k:v for k,v in code.items() if k!='file_hashes'},'configuration_hash':configuration_hash,'executed_at_utc':stamp})
    (output/f'results.{args.mode}.json').write_text(json.dumps(rows,indent=2)+'\n')
    # Phase 01 has no mandatory live tests. Later phases combine both modes per ID;
    # source phases specify which IDs require live execution in acceptance_modes.json.
    modes_path=ROOT/'tests'/f'phase_{args.phase}'/'acceptance_modes.json'
    requirements=json.loads(modes_path.read_text()) if modes_path.exists() else {r['test_id']:['offline'] for r in rows}
    combined=[]
    for row in rows:
        requirements_for_id=requirements.get(row['test_id'],['offline','live'])
        found=[]
        for mode in requirements_for_id:
            path=output/f'results.{mode}.json'
            if path.exists():
                found.extend(r for r in json.loads(path.read_text()) if r['test_id']==row['test_id'])
        fresh=len(found)==len(requirements_for_id) and all(r['code_version']==row['code_version'] and r['configuration_hash']==configuration_hash for r in found)
        status='fail' if any(r['status']=='fail' for r in found) else 'pass' if fresh and all(r['status']=='pass' for r in found) else 'blocked'
        combined.append({**row,'mode':'combined','status':status,'required_modes':requirements_for_id,'observed_result':'; '.join(f"{r['mode']}: {r['observed_result']}" for r in found) or 'Required mode has not executed'})
    (output/'results.json').write_text(json.dumps(combined,indent=2)+'\n')
    print(capture.getvalue())
    for row in combined:
        print(row['test_id'],row['status'])
    return 0 if all(r['status']=='pass' for r in combined) else 1

if __name__=='__main__':
    sys.exit(main())
