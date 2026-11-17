"""Run three explicit small CLI samples with independent report and market-year bounds."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,shlex,sys
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'artifacts/acceptance/phase-06'
results=[]
for family,commodity in [('world-production','Corn'),('grain-trade','Corn'),('oilseed-trade','2222000')]:
 cmd=[sys.executable,'-m','usda_data','fetch','--dataset',family,'--market-years','2025','--commodities',commodity,'--report-start','2026-11-01','--report-end','2026-11-30','--with-reports','--data-dir',str(OUT/'sample/data'),'--output-dir',str(OUT/'sample/exports')]
 result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 (OUT/f'sample-{family}.txt').write_text(result.stdout+result.stderr)
 with (OUT/'commands.txt').open('a') as f:f.write(f'UTC: {datetime.now(timezone.utc).isoformat()}\nWorking directory: {ROOT}\nCommand: {shlex.join(cmd)}\nExit code: {result.returncode}\n\n')
 print(family,result.returncode,result.stdout[-1200:],flush=True);results.append(result.returncode)
raise SystemExit(0 if all(r==0 for r in results) else 1)
