import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY", "").strip()
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()

print("=" * 60)
print("  DIAGNÓSTICO DE CONEXIÓN CON GROQ")
print("=" * 60)

if not env_path.exists():
    print(" Archivo .env no encontrado.")
    print("crea el archivo .env a partir de .env.example:")
    print("cp .env.example .env")
    sys.exit(1)

if not api_key or "tu_clave" in api_key:
    print("Falta configurar GROQ_API_KEY en el archivo .env.")
    print("Obtén una clave gratis en: https://console.groq.com/keys")
    sys.exit(1)

print(f"Archivo .env detectado.")
print(f"Clave detectada: {api_key[:8]}...{api_key[-4:]} (longitud: {len(api_key)})")
print(f"Modelo configurado: {model}")

try:
    from groq import Groq, AuthenticationError, RateLimitError, APIConnectionError
except ImportError:
    print("La librería 'groq' no está instalada. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

client = Groq(api_key=api_key)

print("\n1. Verificando autenticación con Groq...")
try:
    models_page = client.models.list()
    active_models = [m.id for m in models_page.data]
    print("✔ ¡Autenticación exitosa! La API Key es válida.")
except AuthenticationError:
    print("\n ERROR 401: Invalid API Key")
    print("   La clave 'GROQ_API_KEY' configurada en .env fue rechazada por Groq.")
    print("   Posibles causas:")
    print("   - Se copió incompleta o con un espacio.")
    print("   - Fue eliminada o revocada en la consola de Groq.")
    print("\n    Solución: Entra a https://console.groq.com/keys , crea una clave nueva y pégala en .env")
    sys.exit(1)
except APIConnectionError as e:
    print(f"\n Error de red / conexión al conectar con api.groq.com: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n Error inesperado al verificar modelos: {e}")
    sys.exit(1)

print(f"\n2. Probando inferencia con el modelo '{model}'...")
try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": 'Responde en formato JSON: {"test": "ok"}'}],
        response_format={"type": "json_object"}
    )
    print(" Respuesta recibida exitosamente:")
    print(response.choices[0].message.content)
    print("\n ¡TODO FUNCIONA CORRECTAMENTE CON GROQ!")
except RateLimitError as e:
    print(f"\n Límite de tasa alcanzado para '{model}': {e}")
    print("   Tip: Puedes cambiar GROQ_MODEL en .env a 'llama-3.3-70b-versatile' o 'llama-3.1-8b-instant'.")
except Exception as e:
    print(f"\n Error al invocar el modelo '{model}': {e}")
    if model not in active_models:
        print(f"   Nota: El modelo '{model}' no figura en la lista de modelos de tu cuenta.")
        print(f"   Modelos disponibles destacados: {[m for m in active_models if 'llama' in m or 'gpt-oss' in m][:5]}")
