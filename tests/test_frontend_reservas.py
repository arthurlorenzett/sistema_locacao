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


# --- avaliações ---

from frontend.componentes import data_br, texto_total_avaliacoes  # noqa: E402


def test_total_de_avaliacoes_no_singular_e_plural():
    assert texto_total_avaliacoes(0) == "Sem avaliações"
    assert texto_total_avaliacoes(1) == "1 avaliação"
    assert texto_total_avaliacoes(12) == "12 avaliações"


def test_data_no_formato_brasileiro():
    assert data_br("2026-10-05") == "05/10/2026"
    assert data_br(None) == ""


# --- reservas recorrentes (mensalista) ---

from frontend.componentes import linhas_previa_serie, mensagem_serie, resumo_previa_serie  # noqa: E402


def _data(dia, livre=True, motivo=None, preco=100.0):
    return {"inicio": f"2026-10-{dia:02d}T20:00:00", "fim": f"2026-10-{dia:02d}T21:00:00",
            "disponivel": livre, "motivo": motivo, "preco": preco}


def test_linhas_da_previa_mostram_preco_ou_motivo():
    datas = [_data(6), _data(13, livre=False, motivo="Já existe uma reserva confirmada para este horário.")]
    assert linhas_previa_serie(datas) == [
        ("Ter 06/10 · 20:00–21:00 · R$ 100", True),
        ("Ter 13/10 · 20:00–21:00 — Já existe uma reserva confirmada para este horário.", False),
    ]


def test_resumo_da_previa():
    assert resumo_previa_serie({"datas": [_data(6), _data(13)], "disponiveis": 2, "valor_total": 200.0}) == \
        "2 de 2 datas disponíveis · Total R$ 200"
    assert resumo_previa_serie({"datas": [_data(6), _data(13, livre=False)], "disponiveis": 1, "valor_total": 100.0}) == \
        "1 de 2 datas disponíveis · Total R$ 100"
    assert resumo_previa_serie({"datas": [_data(6, livre=False)], "disponiveis": 0, "valor_total": 0}) == \
        "Nenhuma das datas está disponível."


def test_mensagem_depois_de_reservar_a_serie():
    assert mensagem_serie({"reservas": 4, "recusadas": []}) == "4 reservas confirmadas."
    assert mensagem_serie({"reservas": 1, "recusadas": []}) == "1 reserva confirmada."
    assert mensagem_serie({"reservas": 3, "recusadas": [{"inicio": "2026-10-13T20:00:00", "motivo": "x"}]}) == \
        "3 reservas confirmadas. Ficou de fora: Ter 13/10."
    fora = [{"inicio": "2026-10-13T20:00:00"}, {"inicio": "2026-10-20T20:00:00"}]
    assert mensagem_serie({"reservas": 2, "recusadas": fora}) == \
        "2 reservas confirmadas. Ficaram de fora: Ter 13/10 e Ter 20/10."
