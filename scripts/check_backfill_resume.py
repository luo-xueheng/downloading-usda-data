"""Exercise unchanged processing and failure/resume using real cached ESR observations."""
from pathlib import Path
import json,tempfile
from usda_data.sync import Task,execute,production_runner
from usda_data.sources.fas_esr import SCHEMA
from usda_data.storage import atomic_write,canonical,hash_file

ROOT=Path(__file__).resolve().parents[1]

def main():
    tasks=[Task('esr-107-2010','export-sales',{'commodities':['107'],'market_years':[2010]}),Task('esr-401-2018','export-sales',{'commodities':['401'],'market_years':[2018]})]
    calls=[]
    def cached(task,*,data_dir,output_dir,refresh):
        calls.append(task.task_id)
        return production_runner(task,data_dir=ROOT/'data',output_dir=output_dir,refresh=False)
    with tempfile.TemporaryDirectory(prefix='usda-resume-audit-') as name:
        root=Path(name);data=root/'state';out=root/'exports'
        first=execute(tasks,data_dir=data,output_dir=out,runner=cached,refresh=False)
        assert first['exit_code']==0
        before=(out/'complete.latest.json').read_bytes();manifest=json.loads(before)
        second=execute(tasks,data_dir=data,output_dir=out,runner=cached,refresh=False)
        assert second['status']=='unchanged'
        before=(out/'complete.latest.json').read_bytes()
        def interrupt(stage,task):
            if stage=='after_normalization' and task.task_id==tasks[-1].task_id:raise RuntimeError('Deliberate interruption after real-source normalization')
        partial=execute(tasks,data_dir=data,output_dir=out,runner=cached,refresh=False,failure_hook=interrupt)
        assert partial['exit_code']==1 and (out/'complete.latest.json').read_bytes()==before
        calls.clear();resumed=execute(tasks,data_dir=data,output_dir=out,runner=cached,refresh=False,resume=True)
        assert resumed['exit_code']==0 and calls==[tasks[-1].task_id]
        after=json.loads((out/'complete.latest.json').read_text())
        same={k:v['csv_sha256'] for k,v in manifest['exports'].items()}=={k:v['csv_sha256'] for k,v in after['exports'].items()}
        target=out/after['exports'][tasks[0].task_id]['csv_path']
        import hashlib
        def business_digest(size):
            digest=hashlib.sha256();count=0
            for frame in SCHEMA.read_csv_chunks(target,size):
                for row in frame[[f.name for f in SCHEMA.fields if f.key or f.type in {'integer','decimal'}]].itertuples(index=False,name=None):
                    digest.update(json.dumps([str(x) for x in row]).encode()+b'\n');count+=1
            return count,digest.hexdigest()
        a=business_digest(5000);b=business_digest(37)
        result={'unchanged':second['status']=='unchanged','resume_equal_to_clean':same,'partial_exit_code':partial['exit_code'],'resumed_tasks':calls,'real_source_tasks':[t.task_id for t in tasks],'small_chunk_equal':a==b,'small_chunk_size':37,'default_chunk_size':5000,'rows':a[0],'canonical_sha256':a[1],'source_type':'Real archived API responses; no synthetic business rows'}
        atomic_write(ROOT/'artifacts/acceptance/phase-09/subset_resume.json',canonical(result));print(result)

if __name__=='__main__':main()
