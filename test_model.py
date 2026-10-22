from groq import Groq
import os, json
from dotenv import load_dotenv
load_dotenv()
c = Groq()
r = c.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role":"user","content":'respond with valid JSON: {"test":"ok"}'}],
    response_format={"type":"json_object"}
)
print(r.choices[0].message.content)
