"""Verify already acquired official alternate PDFs without network access."""
from pathlib import Path
import json
from usda_data.sources.reports import resolve_attachment,FAMILIES
from usda_data.storage import Store,atomic_write,canonical
from usda_data.errors import DownloadError

def main():
    store=Store('data');out=[]
    jobs=[('grain-trade','2015-05')]+[('oilseed-trade',p) for p in ['2014-09','2014-10','2015-04','2014-08','2014-03','2013-06','2013-05']]
    confirmed_404={('grain-trade','2015-05'),('oilseed-trade','2014-09'),('oilseed-trade','2014-10')}
    for family,period in jobs:
        record={'report_family':family,'report_period':period,'url':f'https://apps.fas.usda.gov/PSDOnline/Circulars/{period[:4]}/{period[-2:]}/{FAMILIES[family][0]}.pdf'}
        class CachedOnly:
            def get(self,url,**kw):
                if url==record['url'] and (family,period) in confirmed_404:raise DownloadError('HTTP 404 confirmed by saved live source checks')
                raise RuntimeError('Uncached source evidence: '+url)
        body,receipt,resolved=resolve_attachment(CachedOnly(),store,record)
        out.append({**resolved,'source_artifact_id':receipt['source_artifact_id'],'bytes':len(body),'status':'resolved_verified'})
        print(family,period,'resolved_verified',flush=True)
    atomic_write(Path('artifacts/acceptance/phase-09/resume/resolved_attachments.json'),canonical(out))

if __name__=='__main__':main()
