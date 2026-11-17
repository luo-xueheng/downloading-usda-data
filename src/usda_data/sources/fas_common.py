"""Shared authenticated source access; versioned dictionaries and full partitions."""
from pathlib import Path
import json
import os
import tomllib
from contextvars import ContextVar
from contextlib import contextmanager
from ..credentials import load_api_key
from ..config import HTTPConfig
from ..errors import AuthenticationError, ConfigurationError, FormatError
from ..http import HTTPClient
from ..storage import atomic_write, canonical, sha256

BASE='https://api.fas.usda.gov'
_REFRESH_SEEN=ContextVar('fas_refresh_seen',default=None)

@contextmanager
def refresh_operation():
    token=_REFRESH_SEEN.set(set())
    try:yield
    finally:_REFRESH_SEEN.reset(token)


def client_config():
    path=Path(os.environ.get('USDA_DATA_CONFIG','config/datasets.toml'))
    values=tomllib.loads(path.read_text()).get('fas_http',{}) if path.exists() else {}
    try:return HTTPConfig(**values)
    except TypeError:raise ConfigurationError('Unknown FAS HTTP option') from None


def api_key():
    try:return load_api_key()
    except (OSError,ValueError,UnicodeError):
        raise AuthenticationError('USDA_FAS_API_KEY is missing or invalid; configure environment or working-directory .env') from None


def cached_response(store,path,*,client,refresh=False,key=None):
    """Retain byte archives and receipts; no credentials in cache or requests' URLs."""
    if not path.startswith('/api/') or '?' in path or '..' in path:
        raise ConfigurationError('Unexpected FAS API path')
    url=BASE+path;cache=store.root/'manifests/fas/urls'/f'{sha256(url.encode())}.json'
    seen=_REFRESH_SEEN.get();identity=(str(store.root.resolve()),url)
    if cache.exists() and (not refresh or seen is not None and identity in seen):
        receipt=json.loads(cache.read_text());body=store.artifact(receipt['source_artifact_id']).read_bytes()
        return body,receipt
    key=key or api_key()
    body,metadata=client.get(url,expected='json',headers={'X-Api-Key':key,'Accept':'application/json'})
    if key.encode() in body:raise FormatError('Credential appeared in source response; payload not archived')
    receipt=store.raw(body,metadata=metadata)
    if cache.exists():
        previous=json.loads(cache.read_text())
        if previous['source_artifact_id']==receipt['source_artifact_id']:receipt=previous
    atomic_write(cache,canonical(receipt))
    if seen is not None:seen.add(identity)
    return body,receipt


def selected_codes(request,dictionary,code_field,name_field,*,aliases=None):
    codes={str(r[code_field]):r for r in dictionary}
    if request=='all':return list(codes)
    values=request.split(',') if isinstance(request,str) else list(request)
    names={r[name_field].strip().lower():str(r[code_field]) for r in dictionary};names.update(aliases or {})
    result=[]
    for value in values:
        text=str(value).strip();code=text if text in codes else names.get(text.lower())
        if code not in codes:raise ConfigurationError('Unknown source code/name in requested selection')
        if code not in result:result.append(code)
    if not result:raise ConfigurationError('Empty source code selection')
    return result


def marketing_years(values):
    if isinstance(values,str):
        try:
            if ':' in values:
                a,b=map(int,values.split(':'));values=list(range(a,b+1))
            else:values=[int(x) for x in values.split(',')]
        except ValueError:raise ConfigurationError('Marketing years require YYYY,YYYY or YYYY:YYYY') from None
    else:values=list(values)
    if not values or any(type(v) is not int or v<1900 or v>2200 for v in values):
        raise ConfigurationError('Invalid source marketing-year identifiers')
    return sorted(set(values))
