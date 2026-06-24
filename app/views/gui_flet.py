"""Entrypoint do frontend Flet — Sistema de Locação de Espaços Esportivos.

A aplicação foi refatorada em um pacote modular (ver `frontend/`). Este arquivo
apenas inicializa o Flet. É mantido como ponto de entrada para preservar o comando
de deploy existente (Render): `python app/views/gui_flet.py`.

Para rodar localmente:
    pip install -r requirements.txt
    # opcional: apontar para o backend local
    export API_BASE="http://localhost:5000"
    python app/views/gui_flet.py
"""

import os
import sys

# Garante que o pacote `frontend` (irmão deste arquivo) seja importável tanto ao
# executar diretamente quanto via outras formas de invocação.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft

from frontend.app import main


if __name__ == "__main__":
    # O Render injeta a porta via variável de ambiente PORT; localmente usa 8000.
    porta = int(os.environ.get("PORT", 8000))
    ft.run(main)
