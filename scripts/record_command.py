"""Run a local acceptance command and save its exact argv, output and exit status."""
import argparse,json,os,shlex,subprocess,sys,time,resource
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',default='09',choices=['09','10'])
    parser.add_argument('--name',required=True)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Command required after --')
    if any('API_KEY=' in word for word in command):parser.error('Pass credentials through the existing environment, never command arguments')
    out=ROOT/'artifacts/acceptance'/f'phase-{args.phase}';out.mkdir(exist_ok=True,parents=True)
    capture=out/(args.name+'.txt');started=datetime.now(timezone.utc).isoformat();tick=time.monotonic()
    with capture.open('w') as stream:result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    record={'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'working_directory':str(ROOT),'command':command,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-tick,'output':str(capture.relative_to(ROOT)),'child_peak_rss_mib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/(1024*1024 if sys.platform=='darwin' else 1024)}
    (out/(args.name+'.command.json')).write_text(json.dumps(record,indent=2)+'\n')
    with (out/'commands.txt').open('a') as stream:stream.write(f'UTC: {started}\nWorking directory: {ROOT}\nCommand: {shlex.join(command)}\nExit code: {result.returncode}\nOutput: {capture.relative_to(ROOT)}\n\n')
    print(json.dumps(record,indent=2));return result.returncode

if __name__=='__main__':raise SystemExit(main())
