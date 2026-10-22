# src/priv_audit/llm.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("Falta la GROQ_API_KEY en el archivo .env")

# LLM para auditoria estructurada (devuelve JSON)
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.1,
    model_kwargs={"response_format": {"type": "json_object"}}
)

# LLM para chat libre (RAG, respuestas en texto natural)
llm_chat = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
)
