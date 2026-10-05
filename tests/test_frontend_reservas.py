import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "views"))

from frontend.componentes import descricao_confianca  # noqa: E402
from frontend.tema import COR_AVISO, COR_ERRO, COR_SUCESSO, COR_TEXTO_SUAVE  # noqa: E402


def _c(comp, faltas, pct):
    return {"comparecimentos": comp, "faltas": faltas, "percentual": pct}


def test_cliente_novo():
    assert descricao_confianca(_c(0, 0, None)) == ("Cliente novo (sem histórico)", COR_TEXTO_SUAVE)
    assert descricao_confianca(None) == ("Cliente novo (sem histórico)", COR_TEXTO_SUAVE)


def test_faixas_de_confianca():
    assert descricao_confianca(_c(9, 1, 90)) == ("90% de comparecimento (9 de 10)", COR_SUCESSO)
    assert descricao_confianca(_c(2, 1, 67)) == ("67% de comparecimento (2 de 3)", COR_AVISO)
    assert descricao_confianca(_c(1, 2, 33)) == ("33% de comparecimento (1 de 3)", COR_ERRO)
