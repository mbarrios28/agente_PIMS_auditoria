"""Entrada alternativa al agente de riesgos de GESTITEL."""
import os
from web_app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
