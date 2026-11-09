"""Verified logical snapshots for PostgreSQL; SQLite keeps its original workflow."""
import hashlib
import io
import json
import re
import secrets
import zipfile
from backend.core import ROOT, Error, connect, now, rows, one, get, insert, audit
from backend.storage import read_backup

SCHEMA=ROOT/'backend/schema_postgresql.sql'
TABLES=re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)',(ROOT/'backend/schema.sql').read_text(encoding='utf8'))
SIGNATURE=hashlib.sha256(SCHEMA.read_bytes()).hexdigest()

def set_sequences(c):
    for table in TABLES:
        if table=='sesiones':
            continue
        c.execute("SELECT setval(pg_get_serial_sequence(?, 'id'), GREATEST(COALESCE((SELECT MAX(id) FROM "+table+"),0),1), EXISTS(SELECT 1 FROM "+table+"))",(table,))

def make_backup(c,u,name):
    # A second connection reads a committed, consistent snapshot; the caller owns the write lock.
    with connect() as source:
        source.raw.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        tables={table:rows(source,'SELECT * FROM '+table) for table in TABLES}
        files={r['nombre']:bytes(r['contenido']) for r in rows(source,'SELECT nombre,contenido FROM archivos_contenido')}
    payload=json.dumps({'format':'saique-postgresql','version':2,'schema_sha256':SIGNATURE,'tables':tables},ensure_ascii=False,separators=(',',':')).encode('utf8')
    parts={'database.json':payload,**{'archivos/'+name:content for name,content in files.items()}}
    manifest={'version':2,'files':{k:hashlib.sha256(v).hexdigest() for k,v in parts.items()}}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for key,value in parts.items():z.writestr(key,value)
        z.writestr('manifest.json',json.dumps(manifest))
    content=out.getvalue();filename=secrets.token_hex(16)+'.zip'
    c.execute('INSERT INTO respaldos_contenido(nombre,contenido) VALUES(?,?)',(filename,content))
    ident=insert(c,'respaldos',dict(nombre=name,ubicacion=filename,checksum=hashlib.sha256(content).hexdigest(),fecha=now(),responsable_id=u['id']))
    audit(c,u,'administracion','Realizar backup',ident,'Copia lógica PostgreSQL y archivos con hashes verificados',entity='respaldos')
    from backend.modules.administracion import public_backup
    return public_backup(get(c,'respaldos',ident))

def decode_snapshot(content):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        manifest=json.loads(z.read('manifest.json'))
        if manifest.get('version')!=2 or 'database.json' not in manifest.get('files',{}):
            raise Error('Este respaldo no corresponde al formato PostgreSQL de la instalación.')
        verified={}
        for name,digest in manifest['files'].items():
            if name!='database.json' and not re.fullmatch(r'archivos/[a-f0-9]+\.(png|jpg|webp|pdf|mp4)',name):
                raise Error('El respaldo contiene rutas no admitidas.')
            data=z.read(name)
            if hashlib.sha256(data).hexdigest()!=digest:
                raise Error('El respaldo no superó la comprobación de hashes.')
            verified[name]=data
    snapshot=json.loads(verified.pop('database.json'))
    if snapshot.get('format')!='saique-postgresql' or snapshot.get('schema_sha256')!=SIGNATURE or set(snapshot.get('tables',{}))!=set(TABLES):
        raise Error('La estructura del respaldo no coincide con esta versión.')
    return snapshot,verified

def restore_backup(c,u,d):
    from backend.core import confirm
    from backend.modules.administracion import admin_survives
    from backend.database import WRITE_LOCK
    confirm(d);original=get(c,'respaldos',d.get('respaldo_id'));content=read_backup(c,original['ubicacion'])
    if hashlib.sha256(content).hexdigest()!=original['checksum']:
        raise Error('La firma del respaldo no coincide.')
    snapshot,files=decode_snapshot(content)
    # Session lock covers the commit that preserves the pre-restore backup.
    c.raw.execute('SELECT pg_advisory_lock(%s)',(WRITE_LOCK,))
    previous=None
    try:
        previous=make_backup(c,u,'Antes de restaurar '+original['nombre'])
        c.commit();c.begin_write()
        registry=rows(c,'SELECT * FROM respaldos')
        prior_record=next(r for r in registry if r['id']==previous['id'])
        c.execute('TRUNCATE '+','.join(TABLES)+',archivos_contenido RESTART IDENTITY')
        for table in TABLES:
            if table=='sesiones':continue
            for row in snapshot['tables'][table]:
                columns=list(row)
                if not all(re.fullmatch(r'[a-z_]+',col) for col in columns):
                    raise Error('El respaldo contiene columnas inválidas.')
                c.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',tuple(row.values()))
        admin_survives(c)
        for name,data in files.items():
            c.execute('INSERT INTO archivos_contenido(nombre,contenido,checksum) VALUES(?,?,?)',(name.split('/')[1],data,hashlib.sha256(data).hexdigest()))
        fallback=c.execute("SELECT u.id FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND u.estado='Activo' ORDER BY u.id LIMIT 1").fetchone()[0]
        set_sequences(c)
        for r in registry:
            if not one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(r['ubicacion'],)):
                insert(c,'respaldos',{k:v for k,v in r.items() if k!='id'}|{'responsable_id':fallback})
        saved=one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(original['ubicacion'],))
        prior=one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(prior_record['ubicacion'],))
        ident=insert(c,'restauraciones',dict(respaldo_id=saved['id'],responsable_id=fallback,copia_previa_id=prior['id'],estado='Verificada',inicio=now(),fin=now(),resultado='Filas, relaciones y archivos recuperados en PostgreSQL'))
        audit(c,dict(id=fallback),'administracion','Restaurar sistema',ident,'Restauración PostgreSQL verificada; sesiones cerradas',entity='restauraciones')
        c.execute('INSERT INTO restauraciones_externas(fecha,usuario,respaldo,resultado,copia_previa_id) VALUES(?,?,?,?,?)',(now(),u['usuario'],original['nombre'],'Verificada',prior['id']))
        c.commit()
        return dict(mensaje='Restauración verificada. Iniciá sesión nuevamente.',reiniciar_sesion=True,copia_previa=prior['id'])
    except Exception:
        c.rollback()
        # The whole restore is one database transaction: rollback keeps the previous state and files.
        c.execute('INSERT INTO restauraciones_externas(fecha,usuario,respaldo,resultado,copia_previa_id) VALUES(?,?,?,?,?)',(now(),u['usuario'],original['nombre'],'Falló; cambios revertidos',previous['id'] if previous else None))
        c.commit()
        raise
    finally:
        c.raw.execute('SELECT pg_advisory_unlock(%s)',(WRITE_LOCK,))
