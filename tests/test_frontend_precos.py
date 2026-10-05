import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "views"))

from frontend.agenda import valor_reserva  # noqa: E402
from frontend.componentes import moeda, resumo_regras_preco, rotulo_dias, texto_preco  # noqa: E402
from frontend.telas.locador import _editor_regras_preco  # noqa: E402


class _Pagina:
    def update(self):
        pass


def _regra(dias, inicio="18:00", fim="23:00", preco=180.0):
    return {"dias": dias, "inicio": inicio, "fim": fim, "preco_hora": preco}


# --- textos ---

def test_moeda_sem_centavos_quando_inteiro():
    assert moeda(120) == "R$ 120"
    assert moeda(82.5) == "R$ 82,50"


def test_rotulo_dos_dias():
    assert rotulo_dias([0, 1, 2, 3, 4]) == "Seg a Sex"
    assert rotulo_dias([5, 6]) == "Sáb e Dom"
    assert rotulo_dias([2]) == "Qua"
    assert rotulo_dias([0, 2, 4]) == "Seg, Qua e Sex"
    assert rotulo_dias(list(range(7))) == "Todos os dias"


def test_texto_do_preco_mostra_faixa_quando_ha_regras():
    assert texto_preco({"preco_hora": 120}) == "R$ 120/hora"
    assert texto_preco({"preco_hora": 120, "preco_minimo": 120, "preco_maximo": 120}) == "R$ 120/hora"
    assert texto_preco({"preco_hora": 120, "preco_minimo": 80, "preco_maximo": 180}) == "R$ 80–180/hora"


def test_resumo_das_regras():
    assert resumo_regras_preco([_regra([5, 6]), _regra([0], "08:00", "12:00", 60)]) == [
        "Sáb e Dom, 18:00–23:00: R$ 180/hora", "Seg, 08:00–12:00: R$ 60/hora"]


def test_valor_da_reserva_soma_o_preco_de_cada_hora():
    grade = [{"inicio": "17:00", "preco": 100.0}, {"inicio": "18:00", "preco": 180.0}, {"inicio": "19:00", "preco": 180.0}]
    assert valor_reserva(grade, 0, 2) == 280.0
    assert valor_reserva(grade, 1, 2) == 360.0


# --- editor de regras do formulário do locador ---

def _linha(controle, n=0):
    """Controles da n-ésima regra: (checkboxes dos dias, início, fim, preço)."""
    linha = controle.controls[2].controls[n]
    return linha.data


def test_editor_sem_regras_devolve_lista_vazia():
    _, coletar = _editor_regras_preco(_Pagina(), None)
    assert coletar() == []


def test_editor_carrega_e_devolve_regras_existentes():
    _, coletar = _editor_regras_preco(_Pagina(), [_regra([5, 6])])
    assert coletar() == [_regra([5, 6])]


def test_editor_aceita_virgula_no_preco():
    controle, coletar = _editor_regras_preco(_Pagina(), [_regra([0])])
    _linha(controle)["preco"].value = "82,50"
    assert coletar()[0]["preco_hora"] == 82.5


def test_editor_exige_dia_e_preco_valido():
    controle, coletar = _editor_regras_preco(_Pagina(), [_regra([0])])
    _linha(controle)["dias"][0].value = False
    with pytest.raises(ValueError, match="ao menos um dia"):
        coletar()
    _linha(controle)["dias"][0].value = True
    _linha(controle)["preco"].value = "abc"
    with pytest.raises(ValueError, match="preço"):
        coletar()
