"""Locate partition-boundary memory growth during an unchanged report export."""
from pathlib import Path
import argparse,json,resource,sys,tempfile,gc
from usda_data.sync import Task,adapter_frames
from usda_data.cli import export_frames
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir',type=Path,required=True)
parser.add_argument('--config',type=Path,default=ROOT/'config/full_backfill.json')
parser.add_argument('--task',default='world-production-full')
args=parser.parse_args()
config=json.loads(args.config.read_text());task=Task(**next(t for t in config['tasks'] if t['task_id']==args.task))
frames,schema=adapter_frames(task,args.data_dir,False);last=0

def tracked():
    global last
    for i,frame in enumerate(frames):
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024)
        if peak>last+5:
            row=frame.iloc[0].to_dict() if len(frame) else {}
            print(json.dumps({'partition_index':i,'peak_mib':peak,'rows':len(frame),'period':row.get('report_period'),'year':row.get('period_label'),'commodity':row.get('commodity_code')}),flush=True);last=peak
        yield frame
    print('Finished iterator',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
with tempfile.TemporaryDirectory(prefix='usda-profile-') as name:
    result=export_frames(tracked(),name,dataset=task.dataset,schema=schema)
print(json.dumps(result),flush=True)
