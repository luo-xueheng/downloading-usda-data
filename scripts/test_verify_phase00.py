#!/usr/bin/env python3
"""Exercise Phase 00 verifier rejection paths in an isolated temporary copy.

These deliberately corrupted test cases are synthetic; they never count as
USDA observations, and the frozen originals are never edited.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('phase00',ROOT/'scripts/verify_phase00.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
results=[]

def no_network(*args,**kwargs):
    raise AssertionError('Offline verifier attempted a network request')

urllib.request.urlopen=no_network
with tempfile.TemporaryDirectory(prefix='usda-phase00-verifier-') as td:
    tmp=Path(td).resolve()
    for folder in ['config','docs','scripts','tests/fixtures','artifacts/acceptance/phase-00/discovery']:
        shutil.copytree(ROOT/folder,tmp/folder)
    v.ROOT=tmp
    for test,fn in v.CHECKS:fn()
    results.append({'case':'offline baseline with network forbidden','status':'pass'})

    def case(name,relative,mutation,check,rejected=True):
        p=tmp/relative;original=p.read_bytes()
        catpath=tmp/'tests/fixtures/catalog.json';catbytes=catpath.read_bytes()
        try:
            mutation(p)
            if relative=='tests/fixtures/references/observations.json':
                cat=json.loads(catbytes);cat['references_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
                catpath.write_text(json.dumps(cat))
            try:check()
            except v.InvalidEvidence:
                if not rejected:raise
                results.append({'case':name,'status':'pass','observation':'deliberate corruption rejected'})
            else:
                if rejected:raise AssertionError(name+' incorrectly passed')
        finally:
            p.write_bytes(original);catpath.write_bytes(catbytes)

    def mutate_json(transform):
        def apply(p):
            obj=json.loads(p.read_text());transform(obj);p.write_text(json.dumps(obj))
        return apply

    case('missing dataset','config/scope.json',mutate_json(lambda s:s['datasets'].pop()),v.check_scope)
    case('missing discovered file','config/expected_coverage.json',mutate_json(lambda s:s['files'].pop()),v.check_scope)
    case('broken discovery falsely marked verified','config/source_registry.json',mutate_json(lambda s:s['sources'][0].update(verified_discovery=s['sources'][5]['landing_evidence'])),v.check_sources)
    case('missing publication locator','config/source_registry.json',mutate_json(lambda s:s['publication_claims'][0]['evidence'].update(locator='')),v.check_publications)
    case('damaged holdout bytes','tests/fixtures/raw/wasde-holdout.xml',lambda p:p.write_bytes(p.read_bytes()+b'corruption'),v.check_artifacts)
    case('incorrect expected value even after repinning reference file','tests/fixtures/references/observations.json',mutate_json(lambda s:s['observations'][0].update(expected_value='999999')),v.check_references)
    case('incorrect business dimension even after repinning reference file','tests/fixtures/references/observations.json',mutate_json(lambda s:s['observations'][0]['dimensions'].update(geography='Wrong geography')),v.check_references)
    case('credential assignment','docs/credential_setup.md',lambda p:p.write_text(p.read_text()+'\n'+ 'USDA_FAS_API_KEY'+' = "'+'synthetic_dummy_value_for_test_only'+'"\n'),v.check_secrets)

out=ROOT/'artifacts/acceptance/phase-00/verifier_selftests.json'
out.write_text(json.dumps({'synthetic_negative_cases':True,'production_files_modified':False,'results':results},indent=2)+'\n')
print(f'{len(results)} verifier self-checks passed, including offline network prohibition and deliberate evidence corruption.')
