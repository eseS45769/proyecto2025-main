"""PostgreSQL storage with the application's existing DB-API call shapes."""
import re
import sqlite3
from decimal import Decimal
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parent.parent

class Row(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)

def row_factory(cursor):
    names = [col.name for col in cursor.description]
    def make(values):
        values = [int(v) if isinstance(v, Decimal) and v == v.to_integral_value() else float(v) if isinstance(v, Decimal) else v for v in values]
        return Row(zip(names, values))
    return make

class Result:
    def __init__(self, records=()):
        self.records = iter(records)
        self.lastrowid = None
        self.rowcount = 0
    def fetchone(self):
        return next(self.records, None)
    def fetchall(self):
        return list(self.records)
    def __iter__(self):
        return self.records

def parameters(sql):
    # Question marks inside SQL string literals are text, not bind parameters.
    pieces = re.split(r"('(?:''|[^'])*')", sql)
    return ''.join(p if i % 2 else p.replace('?', '%s') for i, p in enumerate(pieces)).replace('%', '%%').replace('%%s', '%s')

class Connection:
    def __init__(self, url):
        self.raw = psycopg.connect(url, connect_timeout=15, row_factory=row_factory)
    def __enter__(self):
        return self
    def __exit__(self, typ, value, tb):
        try:
            self.rollback() if typ else self.commit()
        finally:
            self.close()
    def close(self):
        self.raw.close()
    def commit(self):
        self.raw.commit()
    def rollback(self):
        self.raw.rollback()
    def execute(self, sql, args=()):
        normalized = sql.strip().rstrip(';').upper()
        if normalized == 'BEGIN IMMEDIATE':
            # Serialize business writes across all Render processes, as SQLite did.
            return self.raw.execute('SELECT pg_advisory_xact_lock(20251109)')
        if normalized in ('PRAGMA JOURNAL_MODE=WAL', 'PRAGMA FOREIGN_KEY_CHECK'):
            return Result()
        if normalized == 'PRAGMA INTEGRITY_CHECK':
            self.raw.execute('SET CONSTRAINTS ALL IMMEDIATE')
            return Result([Row(result='ok')])
        if normalized == "SELECT NAME FROM SQLITE_MASTER WHERE TYPE='TABLE'":
            return self.raw.execute("SELECT table_name AS name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
        try:
            return self.raw.execute(parameters(sql), args)
        except psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
    def executescript(self, sql):
        for statement in sql.split(';'):
            if statement.strip():
                self.raw.execute(statement)
    def backup(self, target):
        # Export a transactionally consistent portable snapshot, compatible with
        # existing verified ZIP backups and the SQLite recovery tooling.
        with psycopg.connect(self.raw.info.dsn, row_factory=row_factory) as source:
            source.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            target.executescript((ROOT/'backend/schema.sql').read_text())
            for table in tables():
                records = source.execute(f'SELECT * FROM {table}').fetchall()
                if records:
                    columns = list(records[0])
                    target.executemany(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', [tuple(r.values()) for r in records])
            target.commit()

def tables():
    return re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', (ROOT/'backend/schema.sql').read_text())

def import_sqlite(source, target, *, replace=False):
    """Preserve identifiers; import into empty storage unless restore is explicit."""
    if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or source.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('El archivo SQLite no supera la verificación de integridad.')
    target.execute('BEGIN IMMEDIATE')
    names = tables()
    if replace:
        target.raw.execute('TRUNCATE '+','.join(names)+' RESTART IDENTITY')
    elif any(target.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in names):
        raise ValueError('La base de destino debe estar vacía; no se sobrescribieron datos.')
    for table in names:
        cursor = source.execute(f'SELECT * FROM {table}')
        columns = [d[0] for d in cursor.description]
        for row in cursor:
            target.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', tuple(row))
        if 'id' in columns:
            target.raw.execute("SELECT setval(pg_get_serial_sequence(%s,'id'), COALESCE((SELECT MAX(id) FROM "+table+"),1), EXISTS(SELECT 1 FROM "+table+"))", (table,))
    target.raw.execute('SET CONSTRAINTS ALL IMMEDIATE')

def restore_into(source, target):
    if isinstance(target, Connection):
        import_sqlite(source, target, replace=True)
    else:
        source.backup(target)
