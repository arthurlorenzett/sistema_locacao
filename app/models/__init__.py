"""
Ponto de centralização dos modelos do domínio.
Facilita a importação em lote das tabelas pelo ecossistema do Flask e do Migrate.
"""

from app.models.usuario_model import Usuario, Locatario, Locador, Administrador
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.models.reserva_model import Reserva

__all__ = [
    "Usuario",
    "Locatario",
    "Locador",
    "Administrador",
    "EspacoEsportivo",
    "Reserva",
]