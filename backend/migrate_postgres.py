"""Import a verified SQLite database into an EMPTY PostgreSQL database.

DATABASE_URL must be a direct PostgreSQL URL. Optional SAIQUE_ADMIN_PASSWORD
changes admin's password in the same transaction and revokes its sessions.
Run: python -m backend.migrate_postgres /path/to/database.sqlite3
"""
import argparse
import os
import sqlite3
from pathlib import Path
from backend.core import ROOT, hash_password
from backend.postgres import Connection, import_sqlite, tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error('No existe la base SQLite de origen.')
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        parser.error('Falta DATABASE_URL.')
    with sqlite3.connect(f'file:{args.source.resolve()}?mode=ro', uri=True) as source:
        with Connection(url) as target:
            target.executescript((ROOT/'backend/schema_postgres.sql').read_text())
            import_sqlite(source, target)
            for table in tables():
                expected = source.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                actual = target.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                if actual != expected:
                    raise RuntimeError(f'Conteo incorrecto en {table}; transacción cancelada.')
            password = os.environ.get('SAIQUE_ADMIN_PASSWORD')
            if password:
                admin = target.execute("SELECT id FROM usuarios WHERE usuario='admin'").fetchone()
                if not admin:
                    raise RuntimeError('No existe admin; transacción cancelada.')
                target.execute('UPDATE usuarios SET password_hash=? WHERE id=?', (hash_password(password), admin['id']))
                target.execute('DELETE FROM sesiones WHERE usuario_id=?', (admin['id'],))
    print('Importación confirmada: tablas verificadas; origen conservado.')

if __name__ == '__main__':
    main()
