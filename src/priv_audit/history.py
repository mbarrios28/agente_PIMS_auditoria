"""Historial persistente local en SQLite; una conexión por operación."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_PATH = Path(__file__).resolve().parents[2] / 'data/history.sqlite3'


@contextmanager
def connect():
    path = Path(os.getenv('PIMS_HISTORY_DB', str(DEFAULT_PATH)))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY, fecha TEXT NOT NULL, tipo TEXT NOT NULL,
                objetivo TEXT NOT NULL, estado TEXT NOT NULL, resultado TEXT NOT NULL)''')
            yield connection
    finally:
        connection.close()



def save(kind, objective, result, status='completado', key=None):
    key = key or str(uuid4())
    with connect() as db:
        db.execute('INSERT INTO history VALUES (?, ?, ?, ?, ?, ?)',
                   (key, datetime.now(timezone.utc).isoformat(), kind, objective,
                    status, json.dumps(result, ensure_ascii=False)))
    return key


def list_entries(limit=50, offset=0, kind=None):
    with connect() as db:
        where, params = (' WHERE tipo = ?', (kind,)) if kind else ('', ())
        total = db.execute('SELECT COUNT(*) FROM history' + where, params).fetchone()[0]
        rows = db.execute('SELECT id, fecha, tipo, objetivo, estado FROM history' + where +
                          ' ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?', (*params, limit, offset)).fetchall()
    return dict(total=total, items=[dict(row) for row in rows])


def get(key):
    with connect() as db:
        row = db.execute('SELECT * FROM history WHERE id = ?', (key,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item['resultado'] = json.loads(item['resultado'])
    return item
