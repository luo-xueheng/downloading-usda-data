from decimal import Decimal
from pathlib import Path
import json
import sqlite3
import xml.etree.ElementTree as ET
import pytest
from usda_data.cli import main
from usda_data.errors import AuthenticationError, DownloadError, ConfigurationError
from usda_data.schema import Schema, Field
from usda_data.sql import connect, import_csv, readback_hash, check_constraints
from usda_data.storage import hash_file

ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.acceptance('P10-A3')
@pytest.mark.acceptance('P10-A4')
def test_synthetic_exact_decimal_null_escape_and_atomic_failure(tmp_path):
    schema = Schema('synthetic_transfer','1',(
        Field('code','string',False,'Synthetic code','synthetic',key=True),
        Field('level','decimal',False,'Synthetic decimal key','synthetic',key=True),
        Field('amount','decimal',True,'Synthetic exact amount','synthetic'),
        Field('label','string',True,'Synthetic escaped text','synthetic'),
    ))
    frame = schema.frame([
        {'code':'001','level':Decimal('0.50'),'amount':Decimal('9007199254740993.1234567890123456789'),'label':'\\N'},
        {'code':'002','level':Decimal('0.50'),'amount':None,'label':''},
        {'code':'003','level':Decimal('0.50'),'amount':Decimal('-0.00'),'label':None},
    ])
    path = tmp_path/'source.csv'
    schema.write_csv(frame,path)
    with connect(':memory:') as db:
        assert import_csv(db,'sample',schema,path,chunk_size=1) == 3
        assert readback_hash(db,'sample',schema)['csv_sha256'] == hash_file(path)
        assert check_constraints(db,'sample',schema)['duplicate_rejected']
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('INSERT INTO sample VALUES (?,?,?,?)',('001','0.500',None,None))
        bad = tmp_path/'bad.csv'
        bad.write_bytes(path.read_bytes()+path.read_bytes().split(b'\n')[1]+b'\n')
        with pytest.raises(sqlite3.IntegrityError):
            import_csv(db,'bad',schema,bad,chunk_size=1)
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='bad'").fetchall()


@pytest.mark.acceptance('P10-A5')
@pytest.mark.parametrize('args', [
    ['fetch','--dataset','all','--config',str(ROOT/'config/full_backfill.json'),'--dry-run','--years','2025'],
    ['fetch','--dataset','wasde'],
    ['fetch','--dataset','wasde','--start','bad','--end','2026-11-10'],
    ['fetch','--dataset','export-sales','--market-years','bad'],
    ['fetch','--dataset','costs-returns','--years','2026:2010'],
    ['fetch','--dataset','rma-sob','--commodity-years','2025','--chunk-size','0'],
])
def test_invalid_cli_returns_two(args,tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([*args,'--data-dir',str(tmp_path/'data'),'--output-dir',str(tmp_path/'exports')])
    assert exc.value.code == 2
    assert not list(tmp_path.rglob('*.latest.json'))


@pytest.mark.acceptance('P10-A5')
@pytest.mark.parametrize('failure',[AuthenticationError,DownloadError])
def test_failed_auth_or_runtime_never_publish_success(failure,monkeypatch,tmp_path,capsys):
    def denied(*args,**kwargs):
        raise failure('Synthetic failure; no real credentials')
    monkeypatch.setattr('usda_data.cli.iter_export_sales',denied)
    assert main(['fetch','--dataset','export-sales','--market-years','2026','--data-dir',str(tmp_path),'--output-dir',str(tmp_path/'out')]) == 1
    assert not list(tmp_path.rglob('*.latest.json'))
    assert 'Synthetic' not in capsys.readouterr().err


@pytest.mark.acceptance('P10-A5')
def test_success_unchanged_partial_exit_codes(monkeypatch,tmp_path):
    assert main(['list-datasets']) == 0
    for status,code in [('complete',0),('unchanged',0),('partial',1)]:
        monkeypatch.setattr('usda_data.sync.execute',lambda *a,**k:{'status':status,'exit_code':code})
        assert main(['sync','--config',str(ROOT/'config/small_sync.json'),'--data-dir',str(tmp_path)]) == code
