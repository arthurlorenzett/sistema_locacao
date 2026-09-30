from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.services import validacao


def _agora_brasilia():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)


def test_agora_usa_horario_de_brasilia_independente_do_servidor():
    # O Render roda em UTC; as datas digitadas pelos usuários são no horário de Brasília.
    assert abs(validacao.agora() - _agora_brasilia()) < timedelta(seconds=5)


def test_rejeita_horario_que_ja_passou_em_brasilia():
    passado = (_agora_brasilia() - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M")
    with pytest.raises(ValueError, match="futuro"):
        validacao.validar_data_horario_futuro(passado)


def test_aceita_horario_futuro_em_brasilia():
    futuro = (_agora_brasilia() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
    assert validacao.validar_data_horario_futuro(futuro) > _agora_brasilia()
