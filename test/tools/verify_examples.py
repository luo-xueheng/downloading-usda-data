"""Run the documented seven-dataset Python and CLI examples from pinned official fixtures.

The fixture seed is explicit: it proves installation and interface reproducibility,
not fresh source availability. Required live suites supply that separate evidence.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import pandas as pd
from usda_data import download_dataset
from usda_data.schema import Schema
from usda_data.storage import Store, atomic_write, canonical, sha256

ROOT = Path(__file__).resolve().parents[2]


def helper(phase, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'test/datasets'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed(data):
    store = Store(data)
    helper('02', 'test_wasde').seed(store)
    helper('03', 'test_ers').seed(store, ['4962','4927','4923','4924'])
    helper('04', 'test_esr').seed(store, ['esr-701-2026'])
    reports = helper('06', 'test_reports')
    for family in reports.reports.FAMILIES:
        reports.seed_reports(store, family)
        reports.seed_psd_sample(store, family)
    rma = helper('07', 'test_rma')
    path, _, _ = rma.artifact('development')
    acquisition = json.loads(Path(str(path)+'.acquisition.json').read_text())
    receipt = store.raw(path.read_bytes(), metadata={'url':acquisition['url']})
    layout = store.raw((ROOT/'test/fixtures/raw/rma-layout.pdf').read_bytes(), metadata={})
    atomic_write(store.root/'manifests/rma-sob/urls'/f'{sha256(acquisition["url"].encode())}.json', canonical(receipt))
    atomic_write(store.root/'manifests/rma-sob/discovery.json', canonical({'years':{'2025':acquisition['url']}, 'layout_artifact_id':layout['source_artifact_id'], 'unsupported_history':{'period':'1948-1988'}}))


def requests():
    cases = [
        ('wasde', {'start':'2026-11-10', 'end':'2026-11-10'}),
        ('costs-returns', {'years':[2025], 'commodities':'Corn'}),
        ('export-sales', {'commodities':['701'], 'market_years':[2026]}),
        ('rma-sob', {'commodity_years':[2025]}),
    ]
    for family in ['world-production','grain-trade','oilseed-trade']:
        cases.append((family, {'market_years':[2025], 'commodities':['2222000' if family=='oilseed-trade' else '0440000'], 'report_start':'2026-11-01', 'report_end':'2026-11-30'}))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = output/'data'
    seed_marker = output/'fixtures-seeded.json'
    if not seed_marker.exists():
        seed(data)
        seed_marker.write_text(json.dumps({'source': 'pinned official fixtures', 'status': 'complete'})+'\n')
    def denied(*args, **kwargs):
        raise AssertionError('Pinned handover examples must never access the network')
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    # The CLI runs in a fresh process outside the repository and gets the same
    # network prohibition. No source checkout is added to its import path.
    guard = output/'network-guard'
    guard.mkdir(exist_ok=True)
    (guard/'sitecustomize.py').write_text('import socket\ndef denied(*a, **k):\n    raise AssertionError("Offline example attempted network")\nsocket.socket.connect=denied\nsocket.socket.connect_ex=denied\nsocket.create_connection=denied\n')
    import os
    env = dict(os.environ, PYTHONPATH=str(guard))
    checks = []
    for dataset, options in requests():
        frame = download_dataset(dataset, data_dir=data, **options)
        command = [sys.executable, '-m', 'usda_data', 'fetch', '--dataset', dataset, '--data-dir', str(data), '--output-dir', str(output/'exports')]
        for key, value in options.items():
            command += ['--'+key.replace('_','-'), ','.join(map(str,value)) if isinstance(value,list) else str(value)]
        result = subprocess.run(command, cwd=output, env=env, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f'{dataset} CLI failed: {result.stderr}')
        manifest = json.loads((output/'exports'/f'{dataset}.latest.json').read_text())
        schema = Schema.load(output/'exports'/manifest['schema_path'])
        other = schema.read_csv(output/'exports'/manifest['csv_path'])
        # Both paths preserve the same source order; exact ordered equality is
        # stronger than equality after sorting, and avoids duplicate full copies.
        pd.testing.assert_frame_equal(frame, other)
        checks.append({'dataset':dataset, 'rows':len(frame), 'options':options, 'command':command, 'exit_code':result.returncode, 'csv_sha256':manifest['csv_sha256'], 'status':'pass'})
        print(dataset, len(frame), 'Python/CLI exact equality', flush=True)
        del frame, other
        import gc
        gc.collect()
    # Public ancillary interfaces must load their bundled metadata from the wheel.
    from usda_data import download_psd, download_reports
    assert len(download_psd(['0440000'], [2025], data_dir=data)) > 0
    assert len(download_reports('world-production', '2026-11-01', '2026-11-30', data_dir=data)) == 1
    (output/'checks.json').write_text(json.dumps({'status':'pass', 'executed_at_utc':datetime.now(timezone.utc).isoformat(), 'python':sys.version, 'checks':checks}, indent=2)+'\n')


if __name__ == '__main__':
    main()
