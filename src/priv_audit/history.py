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


def review(key, reviewer, decision, comment):
    """Registro local de revisión; no equivale a aceptación corporativa del riesgo."""
    import hashlib
    if decision not in ('revisado', 'requiere_cambios'):
        raise ValueError('Decisión de revisión inválida.')
    if not isinstance(reviewer, str) or not 3 <= len(reviewer.strip()) <= 150:
        raise ValueError('Indica el nombre del revisor (3–150 caracteres).')
    if not isinstance(comment, str) or not 3 <= len(comment.strip()) <= 1500:
        raise ValueError('Escribe una observación de revisión (3–1500 caracteres).')
    with connect() as db:
        row = db.execute("SELECT resultado FROM history WHERE id=? AND tipo='riesgos' AND estado='completado'", (key,)).fetchone()
        if not row:
            raise ValueError('Evaluación de riesgos no encontrada o no finalizada.')
        db.execute('''CREATE TABLE IF NOT EXISTS risk_reviews (
            id TEXT PRIMARY KEY, entry_id TEXT NOT NULL, fecha TEXT NOT NULL,
            reviewer TEXT NOT NULL, decision TEXT NOT NULL, comment TEXT NOT NULL, result_hash TEXT NOT NULL)''')
        event = dict(id=str(uuid4()), entry_id=key, fecha=datetime.now(timezone.utc).isoformat(),
                     reviewer=reviewer.strip(), decision=decision, comment=comment.strip(),
                     result_hash=hashlib.sha256(row['resultado'].encode()).hexdigest())
        db.execute('INSERT INTO risk_reviews VALUES (:id,:entry_id,:fecha,:reviewer,:decision,:comment,:result_hash)', event)
    return event


def reviews(key):
    with connect() as db:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='risk_reviews'").fetchone()
        if not exists:
            return []
        return [dict(r) for r in db.execute('SELECT * FROM risk_reviews WHERE entry_id=? ORDER BY fecha,id', (key,))]
