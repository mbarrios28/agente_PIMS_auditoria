"""Groq principal; Gemini optativo con presupuesto local compartido y sin reintentos."""
import json
import os
from threading import Lock
from types import SimpleNamespace

GROQ_MODEL = 'openai/gpt-oss-120b'
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/'
GEMINI_MODEL = 'gemini-3.5-flash-lite'


class EmptyProviderResponse(ConnectionError):
    pass


class FallbackBudgetError(ValueError):
    pass


class FallbackBudget:
    """Reserva antes de enviar: los errores también consumen presupuesto. No es un límite de facturación."""
    def __init__(self, calls=12, characters=160000, output_tokens=12000):
        self.lock = Lock()
        self.limits = (calls, characters, output_tokens)
        self.used = [0, 0, 0]

    def reserve(self, characters, output_tokens):
        with self.lock:
            requested = (1, characters, output_tokens)
            if any(used + value > limit for used, value, limit in zip(self.used, requested, self.limits)):
                raise FallbackBudgetError('Se alcanzó el presupuesto compartido de Gemini. No se envió otra solicitud.')
            self.used = [used + value for used, value in zip(self.used, requested)]


PROCESS_BUDGET = FallbackBudget()


def fallback_eligible(exc):
    code = getattr(exc, 'status_code', None)
    if code is not None:
        return code in (408, 429) or code >= 500
    return isinstance(exc, (TimeoutError, ConnectionError, OSError)) or type(exc).__name__ in {
        'APIConnectionError', 'APITimeoutError', 'ConnectError', 'ConnectTimeout', 'ReadTimeout', 'TimeoutException'}


class ProviderRouter:
    def __init__(self, primary=None, backup=None, budget=None, on_switch=None):
        self.primary, self.backup = primary, backup
        self.budget = budget if budget is not None else PROCESS_BUDGET
        self.on_switch = on_switch
        self.provider, self.model = 'groq', GROQ_MODEL
        self.used_providers = []
        self.calls = self.characters = self.output_reserved = 0
        # Misma interfaz de completions que el agente ya utiliza.
        self.chat = SimpleNamespace(completions=self)

    def _primary(self):
        if self.primary is None:
            from groq import Groq
            self.primary = Groq(api_key=os.environ['GROQ_API_KEY'], timeout=20, max_retries=0)
        return self.primary

    def _backup(self):
        if self.backup is None:
            from openai import OpenAI
            # Endpoint REST compatible de Google, con reintentos desactivados.
            self.backup = OpenAI(api_key=os.environ['GEMINI_API_KEY'], base_url=GEMINI_URL,
                               timeout=25, max_retries=0)
        return self.backup

    def _gemini(self, kwargs):
        params = dict(kwargs)
        params['model'] = os.getenv('GEMINI_MODEL', GEMINI_MODEL)
        params['max_tokens'] = min(int(params.pop('max_completion_tokens', 1024)), 1536)
        params['reasoning_effort'] = 'none' if params['model'].startswith('gemini-2.5') else 'minimal'
        # Contar todo el contexto y los esquemas, sin recortar evidencia silenciosamente.
        characters = len(json.dumps(params, ensure_ascii=False))
        if characters > 24000:
            raise FallbackBudgetError('El contexto excede 24 000 caracteres para el respaldo Gemini. Reduce el alcance.')
        if self.calls >= 6 or self.characters + characters > 80000 or self.output_reserved + params['max_tokens'] > 6000:
            raise FallbackBudgetError('Se alcanzó el presupuesto de Gemini para esta tarea; no se envió otra solicitud.')
        self.budget.reserve(characters, params['max_tokens'])
        self.calls += 1
        self.characters += characters
        self.output_reserved += params['max_tokens']
        self.model = params['model']
        result = self._backup().chat.completions.create(**params)
        if hasattr(result, 'choices'):
            if not result.choices or (not result.choices[0].message.content and not result.choices[0].message.tool_calls):
                raise EmptyProviderResponse()
        if 'gemini' not in self.used_providers:
            self.used_providers.append('gemini')
        return result

    def create(self, **kwargs):
        if self.provider == 'gemini':
            return self._gemini(kwargs)
        try:
            result = self._primary().chat.completions.create(**kwargs)
            if hasattr(result, 'choices'):
                if not result.choices:
                    raise EmptyProviderResponse()
                message = result.choices[0].message
                if not message.content and not message.tool_calls:
                    raise EmptyProviderResponse()
        except Exception as exc:
            if not os.getenv('GEMINI_API_KEY') or not fallback_eligible(exc):
                raise
            self.provider = 'gemini'
            self.model = os.getenv('GEMINI_MODEL', GEMINI_MODEL)
            if self.on_switch:
                self.on_switch()
            return self._gemini(kwargs)
        if 'groq' not in self.used_providers:
            self.used_providers.append('groq')
        return result

    def summary(self):
        return dict(proveedor_actual=self.provider, modelo=self.model,
                    proveedores=self.used_providers, llamadas_gemini=self.calls,
                    caracteres_gemini=self.characters, salida_maxima_reservada=self.output_reserved)
