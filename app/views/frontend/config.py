"""Configurações do frontend.

A URL base da API pode ser sobrescrita pela variável de ambiente `API_BASE`
(útil para apontar para o backend local durante o desenvolvimento), com fallback
para o backend hospedado no Render.
"""

import os

API_BASE = os.environ.get("API_BASE", "http://localhost:5000")
