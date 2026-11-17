"""Execute README CLI examples and its literal Python block with the installed wheel."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    commands = [
        [sys.executable,'-m','usda_data','--help'],
        [str(Path(sys.executable).parent/'usda-data'),'list-datasets'],
        [sys.executable,'-m','usda_data','calendar','--dataset','all'],
        [sys.executable,'-m','usda_data','fetch','--dataset','all','--config','config/full_backfill.json','--dry-run'],
        [sys.executable,'-m','pip','check'],
    ]
    checks = []
    for command in commands:
        result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        assert result.returncode == 0, result.stderr
        checks.append({'command':command,'exit_code':result.returncode,'stdout':result.stdout})
    for block in re.findall(r'```python\n(.*?)```',(ROOT/'README.md').read_text(),re.S):
        result = subprocess.run([sys.executable,'-c',block],cwd=ROOT,capture_output=True,text=True)
        assert result.returncode == 0, result.stderr
        checks.append({'python_example':block,'exit_code':result.returncode})
    out = ROOT/'artifacts/acceptance/phase-10/readme_cli_checks.json'
    out.write_text(json.dumps({'status':'pass','checks':checks},indent=2)+'\n')
    print(f'{len(checks)} README/installation checks passed')


if __name__ == '__main__':
    main()
