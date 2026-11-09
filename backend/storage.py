"""Persistent attachments and backup bytes when PostgreSQL is enabled."""
import hashlib
from backend.core import DATA, Error

def is_cloud(c):
    return getattr(c, 'dialect', None) == 'postgresql'

def save_file(c, name, content):
    if is_cloud(c):
        c.execute('INSERT INTO archivos_contenido(nombre,contenido,checksum) VALUES(?,?,?) ON CONFLICT(nombre) DO UPDATE SET contenido=excluded.contenido,checksum=excluded.checksum',
                  (name,content,hashlib.sha256(content).hexdigest()))
    else:
        (DATA/'archivos'/name).write_bytes(content)

def read_file(c, name):
    if is_cloud(c):
        row=c.execute('SELECT contenido,checksum FROM archivos_contenido WHERE nombre=?',(name,)).fetchone()
        if not row:
            raise Error('Archivo no encontrado.',404)
        content=bytes(row['contenido'])
        if hashlib.sha256(content).hexdigest()!=row['checksum']:
            raise Error('El archivo no superó la verificación de integridad.',500)
        return content
    p=DATA/'archivos'/name
    if not p.is_file():
        raise Error('Archivo no encontrado.',404)
    return p.read_bytes()

def read_backup(c, name):
    if is_cloud(c):
        row=c.execute('SELECT contenido FROM respaldos_contenido WHERE nombre=?',(name,)).fetchone()
        if not row:
            raise Error('El archivo del respaldo no está disponible. Conserva su copia externa.',404)
        return bytes(row['contenido'])
    p=DATA/'respaldos'/name
    if not p.is_file():
        raise Error('El archivo del respaldo no está disponible.',404)
    return p.read_bytes()
