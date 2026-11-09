"""PostgreSQL connection preserving the existing module API and write ordering."""
import os
import re
import sqlite3
from decimal import Decimal

WRITE_LOCK = 739314055

class Row(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)

def row_factory(cursor):
    columns = [item.name for item in cursor.description] if cursor.description else []
    def make(values):
        return Row(zip(columns, (int(v) if isinstance(v, Decimal) and v == v.to_integral_value() else v for v in values)))
    return make

def parameters(sql):
    """Translate only placeholders outside SQL string literals."""
    out=[]; quoted=False; index=0
    while index<len(sql):
        ch=sql[index]
        if ch=="'":
            if quoted and index+1<len(sql) and sql[index+1]=="'":
                out.append("''");index+=2;continue
            quoted=not quoted
        out.append('%s' if ch=='?' and not quoted else ch)
        index+=1
    return ''.join(out)

class PostgresConnection:
    dialect = 'postgresql'
    def __init__(self, url):
        import psycopg
        self.psycopg = psycopg
        # Advisory session locks and search_path require a direct Neon connection.
        # The direct endpoint uses the same database and role; only -pooler is removed.
        from urllib.parse import urlsplit, urlunsplit
        parsed=urlsplit(url)
        if parsed.hostname and parsed.hostname.endswith('.neon.tech') and '-pooler.' in parsed.hostname:
            url=urlunsplit(parsed._replace(netloc=parsed.netloc.replace('-pooler.','.')))
        # Neon requires TLS; never silently fall back to an unencrypted connection.
        self.raw = psycopg.connect(url, sslmode='require', connect_timeout=15,
                                   autocommit=True, row_factory=row_factory)
        schema = os.environ.get('SAIQUE_PG_SCHEMA', 'public')
        if not re.fullmatch(r'[a-z_][a-z0-9_]*', schema):
            raise ValueError('Esquema PostgreSQL inválido.')
        self.raw.execute("SET search_path TO "+schema+"; SET statement_timeout TO '45s'; SET lock_timeout TO '20s'",prepare=False)
    @property
    def in_transaction(self):
        return self.raw.info.transaction_status.name != 'IDLE'
    def begin_write(self):
        if not self.in_transaction:
            self.raw.execute('BEGIN; SELECT pg_advisory_xact_lock('+str(WRITE_LOCK)+')',prepare=False)
    def execute(self, sql, args=()):
        if sql.strip().upper()=='BEGIN IMMEDIATE':
            self.begin_write()
            return self.raw.cursor()
        if re.match(r'^\s*(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER)', sql, re.I):
            self.begin_write()
        try:
            return self.raw.execute(parameters(sql), args or None)
        except self.psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError('El registro incumple una restricción de integridad.') from exc
    def executescript(self, script):
        self.begin_write()
        self.raw.execute(script,prepare=False)
    def commit(self):
        self.raw.commit()
    def rollback(self):
        self.raw.rollback()
    def close(self):
        self.raw.close()
    def __enter__(self):
        return self
    def __exit__(self, typ, value, tb):
        try:
            self.rollback() if typ else self.commit()
        finally:
            self.close()


def cloud_enabled():
    return bool(os.environ.get('DATABASE_URL'))
