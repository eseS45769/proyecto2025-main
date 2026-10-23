import hashlib
import hmac
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('SAIQUE_DATA', str(ROOT / 'data')))
DB = DATA / 'saique.sqlite3'

class Error(Exception):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status

def now():
    return datetime.now(timezone(timedelta(hours=-4))).isoformat(timespec='seconds')

class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()

def connect():
    c = sqlite3.connect(DB, timeout=20, factory=Connection)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=20000')
    return c

def rows(c, sql, args=()):
    return [dict(r) for r in c.execute(sql, args)]

def one(c, sql, args=()):
    r = c.execute(sql, args).fetchone()
    return dict(r) if r else None

def get(c, table, ident):
    r = one(c, f'SELECT * FROM {table} WHERE id=?', (integer(ident),))
    if not r:
        raise Error('El registro seleccionado no existe.', 404)
    return r

def insert(c, table, data):
    fields = ','.join(data)
    return c.execute(f'INSERT INTO {table} ({fields}) VALUES ({",".join("?" for _ in data)})', tuple(data.values())).lastrowid

def update(c, table, ident, data):
    c.execute(f'UPDATE {table} SET {",".join(k+"=?" for k in data)} WHERE id=?', (*data.values(), ident))

def text(d, key, required=True, maximum=1000):
    v = str(d.get(key) or '').strip()
    if required and not v:
        raise Error(f'Completá el campo {key.replace("_", " ")}.')
    if len(v) > maximum:
        raise Error(f'{key}: máximo {maximum} caracteres.')
    return v

def integer(v, minimum=1):
    try:
        n = int(str(v))
    except (TypeError, ValueError):
        raise Error('La cantidad o identificador debe ser un número entero.')
    if n < minimum:
        raise Error(f'El valor debe ser mayor o igual a {minimum}.')
    return n

def money(v, positive=True):
    try:
        d = Decimal(str(v))
        if not d.is_finite() or d != d.quantize(Decimal('.01')) or d < 0 or (positive and d == 0) or d > Decimal('9999999999.99'):
            raise ValueError()
        return int(d * 100)
    except (InvalidOperation, ValueError, TypeError):
        raise Error('Ingresá un importe válido con hasta dos decimales.')

def choice(d, key, options):
    v = text(d, key)
    if v not in options:
        raise Error(f'Valor inválido para {key}.')
    return v

def confirm(d):
    if d.get('confirmar') is not True:
        raise Error('Confirmá expresamente la operación.')

def phone(d):
    p = re.sub(r'[\s()\-]', '', text(d, 'telefono', maximum=25))
    if not re.fullmatch(r'\+?\d{7,15}', p):
        raise Error('El teléfono debe contener entre 7 y 15 dígitos.')
    return p

def url(d, key, required=False):
    v = text(d, key, required, 500)
    if v and not (re.match(r'^https?://[^\s]+$', v) or re.fullmatch(r'/archivos/[a-f0-9]+\.(png|jpg|webp|pdf|mp4)', v)):
        raise Error(f'{key}: utilizá una URL http(s) o un archivo cargado.')
    return v

def hash_password(password):
    if len(password) < 10:
        raise Error('La contraseña debe tener al menos 10 caracteres.')
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 250000).hex()
    return f'pbkdf2_sha256$250000${salt}${digest}'

def check_password(password, encoded):
    try:
        _, rounds, salt, digest = encoded.split('$')
        return hmac.compare_digest(digest, hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex())
    except (ValueError, TypeError):
        return False

def permissions(c, user):
    return [r['codigo'] for r in rows(c, 'SELECT p.codigo FROM permisos p JOIN roles_permisos rp ON p.id=rp.permiso_id WHERE rp.rol_id=?', (user['rol_id'],))]

def authorize(c, user, code):
    if code not in permissions(c, user):
        raise Error('Tu rol no tiene permiso para esta operación.', 403)

def owner(c, user, cliente_id):
    role = get(c, 'roles', user['rol_id'])
    if role['nombre'] == 'Cliente':
        client = get(c, 'clientes', cliente_id)
        if client['usuario_id'] != user['id']:
            raise Error('Solo podés acceder a tus propios documentos.', 403)

def audit(c, user, module, operation, ident=None, detail='Operación confirmada', entity=None):
    entities={'inventario':'ajustes_inventario','administracion':'usuarios','finanzas':'ingresos','sesion':'usuarios'}
    insert(c, 'auditorias', dict(usuario_id=user['id'],entidad=entity or entities.get(module,module),registro_id=ident,accion=operation,modulo=module,operacion=operation,documento_id=ident,detalle=detail,fecha=now()))

def number(c, table, prefix):
    return f'{prefix}-{c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {table}").fetchone()[0]:06d}'

def init():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'archivos').mkdir(exist_ok=True)
    (DATA / 'respaldos').mkdir(exist_ok=True)
    with connect() as c:
        c.executescript((ROOT / 'backend/schema.sql').read_text(encoding='utf-8'))
        c.execute('PRAGMA journal_mode=WAL')
        if c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]:
            return
        from backend.catalog import MODULES
        grants = {
            'Administrador': [f'{m["slug"]}.{i+1}' for m in MODULES for i in range(len(m['children']))],
            'Ventas': ['clientes','pedidos','ventas','pagos','reclamos'],
            'Inventario': ['inventario','productos','proveedores','compras'],
            'Marketing': ['marketing'],
            'Envíos': ['envios'],
            'Cliente': ['pedidos.2','pagos.1','pagos.3','reclamos.1','reclamos.2','ventas.2'],
        }
        for m in MODULES:
            for i, child in enumerate(m['children'], 1):
                insert(c, 'permisos', dict(codigo=f'{m["slug"]}.{i}',descripcion=child))
        for name, codes in grants.items():
            rid = insert(c, 'roles',dict(nombre=name,descripcion=f'Acceso de {name}'))
            for p in rows(c, 'SELECT * FROM permisos'):
                if p['codigo'] in codes or p['codigo'].split('.')[0] in codes:
                    if name == 'Ventas' and p['codigo'] in ('pagos.4','ventas.4'):
                        continue
                    insert(c, 'roles_permisos',dict(rol_id=rid,permiso_id=p['id']))
        admin_role = one(c, 'SELECT id FROM roles WHERE nombre=?', ('Administrador',))['id']
        password = os.environ.get('SAIQUE_ADMIN_PASSWORD')
        if not password:
            import secrets
            password = secrets.token_urlsafe(14)
        insert(c, 'usuarios',dict(rol_id=admin_role,nombre='Administrador',usuario='admin',password_hash=hash_password(password)))
        print(f'Cuenta inicial: admin | Contraseña: {password}', flush=True)
        for name in ('Moderna','Clásica','Infantil','Minimalista','Personalizada'):
            insert(c, 'categorias',dict(nombre=name,descripcion=f'Alfombras {name.lower()}'))
