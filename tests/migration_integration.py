"""Verify every imported row and asset using a temporary SQLite backup and a new PG schema."""
import os,sys,subprocess,tempfile,uuid,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
schema='saique_migration_test_'+uuid.uuid4().hex[:10]
with psycopg.connect(os.environ['DATABASE_URL'],sslmode='require',autocommit=True) as raw:raw.execute('CREATE SCHEMA '+schema)
os.environ['SAIQUE_PG_SCHEMA']=schema
from backend.migrate_snapshot import inspect_archive,apply_archive
from backend.core import connect,Error,one,check_password
from backend.storage import read_file
with tempfile.TemporaryDirectory() as tmp:
 archive=Path(tmp)/'fixture.zip';env=dict(os.environ);env.pop('DATABASE_URL',None);env.pop('SAIQUE_PG_SCHEMA',None)
 made=subprocess.run([sys.executable,'tests/migration_fixture.py',str(archive)],env=env,capture_output=True,text=True)
 if made.returncode:raise RuntimeError(made.stderr)
 inspected=inspect_archive(archive)[2]
 result=apply_archive(archive)
 assert result['verified'] and result['target_counts_before_migration_audit']==inspected['source_counts']|{'sesiones':0}
 with connect() as c:
  assert read_file(c,'ac'*24+'.pdf')==b'%PDF-1.4 evidencia temporal de migracion'
  user=one(c,"SELECT * FROM usuarios WHERE usuario='admin'");assert check_password('PruebasSaique2026!',user['password_hash'])
 try:apply_archive(archive)
 except Error as error:assert 'contiene datos' in str(error)
 else:raise AssertionError('El importador debe rechazar una base que ya contiene datos')
 result['destination_refuses_overwrite']=True;result['schema']=schema
 Path('test-results/migration.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('MIGRATION VERIFIED: filas, identificadores, adjuntos y contraseña protegida; segundo intento rechazado.')
