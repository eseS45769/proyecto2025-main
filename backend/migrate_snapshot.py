"""Inspect or import a verified SQLite ZIP into an EMPTY PostgreSQL database."""
import argparse,hashlib,io,json,re,sqlite3,tempfile,zipfile
from pathlib import Path
from backend.core import connect,ROOT,Error,rows,one,audit
from backend.cloud_backups import TABLES,set_sequences
from backend.storage import save_file

def inspect_archive(path):
    data=path.read_bytes();contents={}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('version')!=1 or 'database.sqlite3' not in manifest.get('files',{}):
            raise Error('Se requiere un respaldo SQLite versión 1 de la aplicación actual.')
        if sum(x.file_size for x in archive.infolist())>512*1024*1024:
            raise Error('El respaldo supera el límite de importación de 512 MB.')
        for name,digest in manifest['files'].items():
            if name!='database.sqlite3' and not re.fullmatch(r'archivos/[a-f0-9]+\.(png|jpg|webp|pdf|mp4)',name):
                raise Error('El respaldo contiene una ruta no admitida.')
            content=archive.read(name)
            if hashlib.sha256(content).hexdigest()!=digest:
                raise Error('El respaldo contiene un archivo cuyo hash no coincide.')
            contents[name]=content
    with tempfile.TemporaryDirectory() as folder:
        dbpath=Path(folder)/'original.sqlite3';dbpath.write_bytes(contents.pop('database.sqlite3'))
        source=sqlite3.connect(f'file:{dbpath.as_posix()}?mode=ro',uri=True);source.row_factory=sqlite3.Row
        try:
            if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or source.execute('PRAGMA foreign_key_check').fetchall():
                raise Error('La base de origen no supera la comprobación de integridad.')
            actual={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if actual!=set(TABLES):raise Error('Las tablas del respaldo no corresponden al proyecto.')
            tables={t:[dict(r) for r in source.execute('SELECT * FROM '+t)] for t in TABLES}
        finally:source.close()
    return tables,contents,{'source_sha256':hashlib.sha256(data).hexdigest(),'source_counts':{t:len(r) for t,r in tables.items()},'files':len(contents),'sessions_to_close':len(tables['sesiones'])}

def apply_archive(path):
    tables,files,report=inspect_archive(path)
    with connect() as c:
        if getattr(c,'dialect',None)!='postgresql':raise Error('La importación exige DATABASE_URL para PostgreSQL.')
        c.executescript((ROOT/'backend/schema_postgresql.sql').read_text(encoding='utf8'))
        occupied={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES}
        if any(occupied.values()) or c.execute('SELECT count(*) FROM archivos_contenido').fetchone()[0]:
            raise Error('La base de destino ya contiene datos; no se sobrescribe ningún registro.')
        for table in TABLES:
            if table=='sesiones':continue
            allowed={r['column_name'] for r in rows(c,'SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=?',(table,))}
            for row in tables[table]:
                if set(row)!=allowed:raise Error('Las columnas de '+table+' no coinciden con la versión actual.')
                c.execute('INSERT INTO '+table+' ('+','.join(row)+') VALUES ('+','.join('?' for _ in row)+')',tuple(row.values()))
        for name,content in files.items():save_file(c,name.split('/')[1],content)
        set_sequences(c)
        from backend.modules.administracion import admin_survives
        admin_survives(c)
        target={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES}
        expected=report['source_counts']|{'sesiones':0}
        if target!=expected:raise Error('Los conteos de origen y destino no coinciden.')
        for table in TABLES:
            if table=='sesiones':continue
            for old in tables[table]:
                if one(c,'SELECT * FROM '+table+' WHERE id=?',(old['id'],))!=old:
                    raise Error('Una fila de '+table+' difiere del respaldo.')
        user=one(c,"SELECT u.* FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND u.estado='Activo' ORDER BY u.id LIMIT 1")
        report['target_counts_before_migration_audit']=target
        report['verified']=True
        audit(c,user,'migracion','Importar respaldo SQLite',detail=json.dumps({'sha256':report['source_sha256'],'files':len(files),'verified':True}),entity='migracion')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('backup',type=Path);p.add_argument('--apply',action='store_true');p.add_argument('--report',type=Path)
    args=p.parse_args();report=apply_archive(args.backup) if args.apply else inspect_archive(args.backup)[2]
    payload=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:args.report.write_text(payload,encoding='utf8')
    print(payload)

if __name__=='__main__':main()
