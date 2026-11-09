"""Create the same initial roles, permissions and categories as the local prototype."""
import os
from backend.core import hash_password,Error

def bulk(c,table,columns,values):
    if not values:return
    placeholder='('+','.join('?' for _ in columns)+')'
    c.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES '+','.join(placeholder for _ in values),tuple(x for row in values for x in row))

def seed(c,modules,grants):
    password=os.environ.get('SAIQUE_ADMIN_PASSWORD')
    if not password:
        raise Error('Base vacía: importa el respaldo existente o define SAIQUE_ADMIN_PASSWORD antes del primer inicio.')
    permissions=[(i+1,f'{m["slug"]}.{op}',child) for i,(m,op,child) in enumerate((m,op,child) for m in modules for op,child in enumerate(m['children'],1))]
    roles=[(i+1,name,f'Acceso de {name}') for i,name in enumerate(grants)]
    bulk(c,'permisos',['id','codigo','descripcion'],permissions)
    bulk(c,'roles',['id','nombre','descripcion'],roles)
    links=[]
    for rid,name,_ in roles:
        codes=grants[name]
        for pid,code,_ in permissions:
            if code in codes or code.split('.')[0] in codes:
                if name=='Ventas' and code in ('pagos.4','ventas.4'):continue
                links.append((rid,pid))
    bulk(c,'roles_permisos',['rol_id','permiso_id'],links)
    bulk(c,'usuarios',['rol_id','nombre','usuario','password_hash'],[(1,'Administrador','admin',hash_password(password))])
    bulk(c,'categorias',['id','nombre','descripcion'],[(i+1,name,f'Alfombras {name.lower()}') for i,name in enumerate(('Moderna','Clásica','Infantil','Minimalista','Personalizada'))])
    for table in ['permisos','roles','categorias']:
        c.execute("SELECT setval(pg_get_serial_sequence(?, 'id'), (SELECT MAX(id) FROM "+table+"))",(table,))
