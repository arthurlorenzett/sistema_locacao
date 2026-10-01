import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "views"))

from frontend.agenda import pode_reservar, periodo_reserva, proximos_dias, rotulo_dia  # noqa: E402


def _slot(inicio, fim, livre=True):
    return {"inicio": inicio, "fim": fim, "disponivel": livre}


GRADE = [_slot("20:00", "21:00"), _slot("21:00", "22:00", livre=False),
         _slot("22:00", "23:00"), _slot("23:00", "24:00")]


def test_proximos_dias_comeca_hoje():
    dias = proximos_dias(date(2026, 10, 5), 3)
    assert dias == [date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7)]


def test_rotulo_dos_dias():
    hoje = date(2026, 10, 5)
    assert rotulo_dia(hoje, hoje) == "Hoje"
    assert rotulo_dia(date(2026, 10, 6), hoje) == "Amanhã"
    assert rotulo_dia(date(2026, 10, 8), hoje) == "Qui 08/10"


def test_pode_reservar_horas_seguidas_livres():
    assert pode_reservar(GRADE, 2, 2) is True        # 22h-24h
    assert pode_reservar(GRADE, 0, 1) is True        # 20h-21h
    assert pode_reservar(GRADE, 0, 2) is False       # 21h está ocupado
    assert pode_reservar(GRADE, 1, 1) is False       # o próprio horário está ocupado
    assert pode_reservar(GRADE, 3, 2) is False       # passa do fechamento


def test_periodo_da_reserva_e_meia_noite_vira_o_dia_seguinte():
    assert periodo_reserva(date(2026, 10, 10), GRADE, 0, 1) == ("2026-10-10T20:00", "2026-10-10T21:00")
    assert periodo_reserva(date(2026, 10, 10), GRADE, 2, 2) == ("2026-10-10T22:00", "2026-10-11T00:00")
