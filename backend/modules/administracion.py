import json
import secrets
import shutil
import tempfile
import zipfile
from backend.business import *
WRITES={1,2,3,4}

def admin_survives(c):
    admins=rows(c,"SELECT u.* FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND r.estado='Activo' AND u.estado='Activo'")
    if not admins or not any(all(f'administracion.{i}' in permissions(c,u) for i in range(1,5)) for u in admins):
        raise Error('Debe quedar al menos un administrador activo con todos los permisos de administración.')

def backup(c,u,name):
    # Los cambios del respaldo se guardan luego de obtener una copia consistente.
    # La conexión lectora evita ejecutar backup sobre una conexión con escritura activa.
    filename=secrets.token_hex(16)+'.zip'
    path=DATA/'respaldos'/filename
    with tempfile.TemporaryDirectory(dir=DATA) as temp:
        dbcopy=Path(temp)/'database.sqlite3'
        source=connect()
        dest=sqlite3.connect(dbcopy)
        try:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or dest.execute('PRAGMA foreign_key_check').fetchall():
                raise Error('La copia no superó la comprobación de integridad.')
        finally:
            dest.close()
            source.close()
        manifest={'version':1,'files':{}}
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(dbcopy,'database.sqlite3')
            manifest['files']['database.sqlite3']=hashlib.sha256(dbcopy.read_bytes()).hexdigest()
            for f in (DATA/'archivos').iterdir():
                if f.is_file():
                    key='archivos/'+f.name
                    z.write(f,key)
                    manifest['files'][key]=hashlib.sha256(f.read_bytes()).hexdigest()
            z.writestr('manifest.json',json.dumps(manifest))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    ident=insert(c,'respaldos',dict(nombre=name,ubicacion=filename,checksum=digest,fecha=now(),responsable_id=u['id']))
    audit(c,u,'administracion','Realizar backup',ident,'Copia de tablas y archivos verificada',entity='respaldos')
    return public_backup(get(c,'respaldos',ident))

def public_backup(r):
    return {k:v for k,v in r.items() if k!='ubicacion'}

def restoration(c,u,d):
    confirm(d)
    original=get(c,'respaldos',d.get('respaldo_id'))
    path=DATA/'respaldos'/original['ubicacion']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=original['checksum']:
        raise Error('El respaldo falta o su firma no coincide.')
    with tempfile.TemporaryDirectory(dir=DATA) as temp:
        staging=Path(temp)
        with zipfile.ZipFile(path) as z:
            manifest=json.loads(z.read('manifest.json'))
            if manifest.get('version')!=1 or 'database.sqlite3' not in manifest.get('files',{}):
                raise Error('Formato de respaldo no reconocido.')
            for name,digest in manifest['files'].items():
                if name!='database.sqlite3' and not re.fullmatch(r'archivos/[a-f0-9]+\.(png|jpg|webp|pdf|mp4)',name):
                    raise Error('El respaldo contiene rutas inválidas.')
                content=z.read(name)
                if hashlib.sha256(content).hexdigest()!=digest:
                    raise Error('Un archivo del respaldo no superó la verificación.')
                target=staging/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(content)
        restored=sqlite3.connect(staging/'database.sqlite3')
        restored.row_factory=sqlite3.Row
        try:
            if restored.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or restored.execute('PRAGMA foreign_key_check').fetchall():
                raise Error('La base de datos del respaldo no es íntegra.')
            expected={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            actual={r[0] for r in restored.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if expected!=actual:
                raise Error('La estructura del respaldo no coincide con esta versión.')
            admin_survives(restored)
            pre=backup(c,u,'Antes de restaurar '+original['nombre'])
            c.commit()
            # Mantener un registro recuperable de respaldos, además del log externo.
            registry=rows(c,'SELECT * FROM respaldos')
            originals=staging/'archivos_previos'
            shutil.copytree(DATA/'archivos',originals)
            prior=staging/'prior.sqlite3'
            previous=sqlite3.connect(prior)
            c.backup(previous)
            previous.close()
            try:
                restored.backup(c)
                for f in (DATA/'archivos').iterdir():
                    if f.is_file():
                        f.unlink()
                for name in manifest['files']:
                    if name.startswith('archivos/'):
                        shutil.copy2(staging/name,DATA/name)
                c.execute('DELETE FROM sesiones')
                # Reconstruir registro sin FK a usuarios desaparecidos del respaldo.
                fallback=c.execute("SELECT u.id FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND u.estado='Activo' LIMIT 1").fetchone()[0]
                for r in registry:
                    current=one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(r['ubicacion'],))
                    if not current:
                        insert(c,'respaldos',{k:v for k,v in r.items() if k!='id'} | {'responsable_id':fallback})
                saved=one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(original['ubicacion'],))
                prior_record=next(r for r in registry if r['id']==pre['id'])
                prior_saved=one(c,'SELECT id FROM respaldos WHERE ubicacion=?',(prior_record['ubicacion'],))
                restoration_id=insert(c,'restauraciones',dict(respaldo_id=saved['id'],responsable_id=fallback,inicio=now(),fin=now(),estado='Verificada',resultado='Tablas y archivos verificados',copia_previa_id=prior_saved['id']))
                audit(c,dict(id=fallback),'administracion','Restaurar sistema',restoration_id,f'Restauración verificada; operador original {u["usuario"]}',entity='restauraciones')
                c.commit()
                if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():
                    raise Error('La restauración no superó la comprobación final.')
                for name,digest in manifest['files'].items():
                    if name.startswith('archivos/') and hashlib.sha256((DATA/name).read_bytes()).hexdigest()!=digest:
                        raise Error('La restauración de archivos falló.')
            except Exception:
                c.rollback()
                previous=sqlite3.connect(prior)
                previous.backup(c)
                previous.close()
                for f in (DATA/'archivos').iterdir():
                    if f.is_file():
                        f.unlink()
                for f in originals.iterdir():
                    shutil.copy2(f,DATA/'archivos'/f.name)
                log_external(u,original,'Falló; estado anterior recuperado',pre['id'])
                raise
            log_external(u,original,'Verificada',pre['id'])
            return dict(mensaje='Restauración verificada. Iniciá sesión nuevamente.',reiniciar_sesion=True,copia_previa=pre['id'])
        finally:
            restored.close()

def log_external(u,backup_record,result,prior):
    with (DATA/'restauraciones.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(fecha=now(),usuario=u['usuario'],respaldo=backup_record['nombre'],resultado=result,copia_previa=prior),ensure_ascii=False)+'\n')

def handle(c,u,op,d):
    if op==1:
        role=get(c,'roles',d.get('rol_id'))
        if role['estado']!='Activo':
            raise Error('El rol no está activo.')
        data=dict(nombre=text(d,'nombre',maximum=120),usuario=text(d,'usuario',maximum=50).lower(),rol_id=role['id'],estado=choice(d,'estado',['Activo','Inactivo']))
        if not re.fullmatch(r'[a-z0-9._-]{3,50}',data['usuario']):
            raise Error('El usuario debe tener entre 3 y 50 letras, números, puntos o guiones.')
        password=text(d,'password',False,200)
        if password:
            data['password_hash']=hash_password(password)
        if d.get('id'):
            ident=get(c,'usuarios',d['id'])['id']
            update(c,'usuarios',ident,data)
        else:
            if not password:
                raise Error('Ingresá la contraseña inicial.')
            ident=insert(c,'usuarios',data)
        if role['nombre']=='Cliente':
            client=get(c,'clientes',d.get('cliente_id'))
            if client['usuario_id'] and client['usuario_id']!=ident:
                raise Error('El cliente ya tiene una cuenta vinculada.')
            c.execute('UPDATE clientes SET usuario_id=NULL WHERE usuario_id=?',(ident,))
            update(c,'clientes',client['id'],dict(usuario_id=ident))
        admin_survives(c)
        c.execute('DELETE FROM sesiones WHERE usuario_id=?',(ident,))
        audit(c,u,'administracion','Gestionar usuarios',ident)
        result=one(c,'SELECT id,nombre,usuario,rol_id,estado FROM usuarios WHERE id=?',(ident,))
        if ident==u['id']:
            result.update(reiniciar_sesion=True,mensaje='Cuenta actualizada. Iniciá sesión nuevamente.')
        return result
    if op==2:
        rid=integer(d.get('rol_id'))
        get(c,'roles',rid)
        codes=d.get('permisos')
        valid={r['codigo']:r['id'] for r in rows(c,'SELECT * FROM permisos')}
        if not isinstance(codes,list) or any(code not in valid for code in codes):
            raise Error('La matriz de permisos contiene códigos inválidos.')
        c.execute('DELETE FROM roles_permisos WHERE rol_id=?',(rid,))
        for code in set(codes):
            insert(c,'roles_permisos',dict(rol_id=rid,permiso_id=valid[code]))
        admin_survives(c)
        audit(c,u,'administracion','Gestionar roles y permisos',rid,entity='roles')
        return dict(rol_id=rid,permisos=codes)
    if op==3:
        confirm(d)
        return backup(c,u,text(d,'nombre',maximum=120))
    return restoration(c,u,d)
