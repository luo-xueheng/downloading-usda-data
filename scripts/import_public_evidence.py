"""Import verified public acquisition receipts into the immutable report URL cache."""
import argparse,json
from pathlib import Path
from usda_data.storage import Store,hash_file,atomic_write,canonical,sha256

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);args=parser.parse_args()
    store=Store('data');count=0
    for path in args.directory.rglob('*.acquisition.json'):
        receipt=json.loads(path.read_text());source=Path(str(path).removesuffix('.acquisition.json'))
        if not source.exists() or hash_file(source)!=receipt.get('sha256'):raise ValueError('Public acquisition artifact/hash mismatch')
        url=receipt['url']
        if not url.startswith(('https://esmis.nal.usda.gov/','https://www.fas.usda.gov/','https://apps.fas.usda.gov/')):continue
        record=store.raw(source.read_bytes(),metadata={'url':url,'status':receipt.get('status'),'content_type':receipt.get('content_type'),'acquisition_receipt':str(path),'source_acquired_at_utc':receipt['checked_at_utc']})
        record['retrieved_at_utc']=receipt['checked_at_utc']
        cache=store.root/'manifests/reports/urls'/f'{sha256(url.encode())}.json'
        if cache.exists() and json.loads(cache.read_text())['source_artifact_id']==record['source_artifact_id']:continue
        atomic_write(cache,canonical(record));count+=1
    print('Verified public artifacts imported:',count)

if __name__=='__main__':main()
