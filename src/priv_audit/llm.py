# src/priv_audit/llm.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)


class LazyChatGroq:
    """Instancia ChatGroq bajo demanda para evitar fallos de importación si no hay clave."""
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._instance = None

    def _get_instance(self):
        if not os.environ.get("GROQ_API_KEY"):
            load_dotenv(_ENV_PATH)
        if not os.environ.get("GROQ_API_KEY"):
            raise ValueError("Falta la GROQ_API_KEY en el archivo .env")
        if self._instance is None:
            model = os.environ.get("GROQ_MODEL", self._kwargs.get("model", "openai/gpt-oss-120b"))
            kwargs = {**self._kwargs, "model": model}
            self._instance = ChatGroq(**kwargs)
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def invoke(self, *args, **kwargs):
        return self._get_instance().invoke(*args, **kwargs)


# LLM para auditoria estructurada (devuelve JSON)
llm = LazyChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.1,
    timeout=90,
    max_retries=1,
    model_kwargs={"response_format": {"type": "json_object"}}
)

# LLM para chat libre (RAG, respuestas en texto natural)
llm_chat = LazyChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    timeout=90,
    max_retries=1,
)
