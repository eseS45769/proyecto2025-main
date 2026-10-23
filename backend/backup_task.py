"""Punto de entrada para un respaldo periódico mediante el programador del sistema."""
from backend.core import *
from backend.modules.administracion import backup

def main():
    init()
    with connect() as c:
        user=one(c,"SELECT u.* FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND r.estado='Activo' AND u.estado='Activo' ORDER BY u.id LIMIT 1")
        if not user:
            raise Error('No existe administrador activo para respaldar.')
        authorize(c,user,'administracion.3')
        c.execute('BEGIN IMMEDIATE')
        result=backup(c,user,'Respaldo periódico '+now())
        print(f'Respaldo {result["id"]}: {result["estado"]}')

if __name__=='__main__':
    main()
