"""Rebuild complete large dataset requests under the memory budget and compare exact hashes."""
from pathlib import Path
import argparse,gc,json,resource,sys,tempfile
from usda_data.sync import Task,production_runner
from usda_data.storage import atomic_write,canonical

ROOT=Path(__file__).resolve().parents[2]

def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--budget-mib',type=int,default=1024)
    parser.add_argument('--output',type=Path,default=Path('.cache/performance/full_export_memory.json'))
    args=parser.parse_args()
    active=json.loads((args.data_dir/'manifests/runs/active.json').read_text());state=json.loads((args.data_dir/'manifests/runs'/f'{active["run_id"]}.json').read_text())
    if state['status']!='complete':raise RuntimeError('A complete run is required for exact-output comparison')
    budget=args.budget_mib
    names=['wasde-full','ers-full']
    for dataset in ['export-sales','rma-sob']:
        names.append(max((k for k,v in state['tasks'].items() if v['definition']['dataset']==dataset),key=lambda k:state['tasks'][k]['export']['rows']))
    names+=['world-production-full','grain-trade-full','oilseed-trade-full'];checks=[]
    for name in names:
        original=state['tasks'][name];task=Task(**original['definition'])
        print('Rebuilding',name,flush=True)
        with tempfile.TemporaryDirectory(prefix='usda-memory-') as temporary:
            result=production_runner(task,data_dir=args.data_dir,output_dir=Path(temporary),refresh=False)
            same=result['csv_sha256']==original['export']['csv_sha256'] and result['rows']==original['export']['rows']
            check={'task_id':name,'dataset':task.dataset,'rows':result['rows'],'csv_sha256':result['csv_sha256'],'matches_complete_run':same,'process_peak_rss_mib':peak()};checks.append(check)
            print(json.dumps(check),flush=True)
            if not same:raise RuntimeError('Memory remediation changed complete output bytes')
        gc.collect()
    measured=peak();result={'peak_rss_mib':measured,'budget_mib':budget,'hashes_match_original_full_run':all(c['matches_complete_run'] for c in checks),'status':'pass' if measured<=budget else 'fail','coverage':'Full WASDE, full ERS, all three full report-family histories, and the largest ESR and RMA task exports; all seven dataset adapters exercised sequentially in one process','partition_memory_policy':'Each yielded partition is written then cyclic PDF/HTML allocations are collected before the next partition','original_failed_trial':'full-fetch-completion.command.json','checks':checks}
    atomic_write(args.output,canonical(result));print(json.dumps(result),flush=True)
    return int(measured>budget)

if __name__=='__main__':raise SystemExit(main())
