"""Ejecuciones acotadas en memoria con traza incremental y caducidad."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from time import monotonic
from uuid import uuid4
from .agent import PrivacyAgent, AgentError
from .service import audit
from . import history
import logging

class RunStore:
    def __init__(self, workers=2, ttl=1800, max_runs=20):
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='privaudit')
        self.workers, self.ttl, self.max_runs = workers, ttl, max_runs
        self.lock, self.runs = Lock(), {}

    def _prune(self):
        now = monotonic()
        for key in list(self.runs):
            item = self.runs[key]
            if item['estado'] in ('completado', 'error') and now - item['_updated'] > self.ttl:
                del self.runs[key]

    def start(self, payload):
        with self.lock:
            self._prune()
            if sum(r['estado'] in ('pendiente', 'ejecutando') for r in self.runs.values()) >= self.workers:
                raise ValueError('Hay dos tareas en curso. Espera a que terminen antes de iniciar otra.')
            while len(self.runs) >= self.max_runs:
                completed = [k for k, r in self.runs.items() if r['estado'] in ('completado', 'error')]
                if not completed:
                    raise ValueError('No hay capacidad para otra tarea.')
                del self.runs[completed[0]]
            key = str(uuid4())
            self.runs[key] = dict(id=key, tarea=payload['tarea'], estado='pendiente', traza=[], _updated=monotonic())
        self.executor.submit(self._run, key, dict(payload))
        return key

    def _update(self, key, **data):
        with self.lock:
            self.runs[key].update(data, _updated=monotonic())

    def _run(self, key, payload):
        self._update(key, estado='ejecutando')
        def on_event(event):
            with self.lock:
                self.runs[key]['traza'].append(deepcopy(event))
                self.runs[key]['_updated'] = monotonic()
        try:
            if payload['tarea'] == 'auditoria':
                result = audit(payload['sql'], 'ai', payload['dialect'], payload['objetivo'], on_event)
            else:
                result = PrivacyAgent(task=payload['tarea'], objective=payload['objetivo'], on_event=on_event,
                                      risk_input=payload.get('risk_input')).run()
            history.save(payload['tarea'], payload['objetivo'] or 'Auditoría SQL', result, key=key)
            self._update(key, estado='completado', resultado=result)
        except (AgentError, ValueError) as exc:
            self._save_error(key, payload, str(exc))
        except Exception:
            self._save_error(key, payload, 'La tarea no pudo completarse. Revisa la conexión y vuelve a intentarlo.')

    def _save_error(self, key, payload, error):
        result = dict(error=error, traza=self.get(key)['traza'])
        try:
            history.save(payload['tarea'], payload['objetivo'] or 'Auditoría SQL', result, status='error', key=key)
        except Exception:
            logging.exception('No se pudo guardar la ejecución en el historial')
        self._update(key, estado='error', error=error)

    def get(self, key):
        with self.lock:
            self._prune()
            value = self.runs.get(key)
            return deepcopy({k: v for k, v in value.items() if not k.startswith('_')}) if value else None

runs = RunStore()
