"""Interfaces compatibles con el chat y prototipo; Groq con respaldo acotado."""
import os
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv
from .providers import ProviderRouter, GROQ_MODEL

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class FallbackChat:
    def __init__(self, structured=False):
        self.structured = structured

    def invoke(self, prompt):
        if not os.getenv('GROQ_API_KEY'):
            raise ValueError('Configura GROQ_API_KEY para usar IA.')
        messages = [{'role':'user', 'content':prompt}] if isinstance(prompt, str) else [
            {'role':role, 'content':content} for role, content in prompt]
        router = ProviderRouter()
        options = dict(model=GROQ_MODEL, messages=messages, temperature=.1 if self.structured else .2,
                       max_completion_tokens=1500 if self.structured else 700, reasoning_effort='low')
        if self.structured:
            options['response_format'] = {'type':'json_object'}
        response = router.create(**options)
        return SimpleNamespace(content=response.choices[0].message.content or '',
                               provider=router.provider, model=router.model, fallback=router.summary())


llm = FallbackChat(structured=True)
llm_chat = FallbackChat()
