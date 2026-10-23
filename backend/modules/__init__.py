from importlib import import_module
from backend.catalog import MODULES
from backend.core import Error,authorize,audit

def dispatch(c,u,slug,operation,data,method):
    spec=next((m for m in MODULES if m['slug']==slug),None)
    if not spec or operation<1 or operation>len(spec['children']):
        raise Error('Operación no encontrada.',404)
    authorize(c,u,f'{slug}.{operation}')
    module=import_module(f'backend.modules.{slug}')
    writing=operation in module.WRITES
    if writing and method!='POST':
        raise Error('Esta operación requiere confirmación mediante POST.',405)
    if not writing and method!='GET':
        raise Error('Esta consulta usa GET.',405)
    if writing:
        c.execute('BEGIN IMMEDIATE')
    try:
        result=module.handle(c,u,operation,data)
        if writing:
            c.commit()
        return result
    except Exception:
        if writing:
            c.rollback()
        raise
