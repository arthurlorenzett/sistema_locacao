import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "views"))

from frontend.componentes import resumo_horarios, texto_hoje  # noqa: E402


def _h(dia, abre, fecha):
    return {"dia_semana": dia, "abre": abre, "fecha": fecha}


def test_agrupa_dias_seguidos_com_mesmo_horario():
    grade = [_h(d, "08:00", "22:00") for d in range(5)] + [_h(5, "09:00", "24:00")]
    assert resumo_horarios(grade) == ["Seg a Sex: 08:00–22:00", "Sáb: 09:00–24:00", "Dom: fechado"]


def test_dois_dias_seguidos_usa_e():
    grade = [_h(0, "10:00", "20:00"), _h(5, "08:00", "18:00"), _h(6, "08:00", "18:00")]
    assert resumo_horarios(grade) == ["Seg: 10:00–20:00", "Ter a Sex: fechado", "Sáb e Dom: 08:00–18:00"]


def test_sem_grade_nao_resume():
    assert resumo_horarios([]) == []


def test_texto_de_hoje():
    grade = [_h(0, "08:00", "22:00")]
    assert texto_hoje(grade, dia_semana=0) == "Hoje: 08:00–22:00"
    assert texto_hoje(grade, dia_semana=1) == "Hoje: fechado"
    assert texto_hoje([], dia_semana=0) is None


# --- editor de horários do formulário do locador ---

from frontend.telas.locador import _editor_horarios  # noqa: E402


class _Pagina:
    def update(self):
        pass


def _linhas(controle):
    return [row.controls for row in controle.controls[2:]]  # [checkbox, abre, "às", fecha]


def test_editor_de_espaco_novo_sugere_todos_os_dias_das_8_as_22():
    _, coletar = _editor_horarios(_Pagina(), None)
    assert coletar() == [_h(d, "08:00", "22:00") for d in range(7)]


def test_editor_carrega_grade_existente_e_deixa_outros_dias_fechados():
    _, coletar = _editor_horarios(_Pagina(), [_h(5, "09:00", "24:00")])
    assert coletar() == [_h(5, "09:00", "24:00")]


def test_editor_recusa_fechamento_antes_da_abertura():
    controle, coletar = _editor_horarios(_Pagina(), [_h(0, "08:00", "22:00")])
    _linhas(controle)[0][3].value = "07:00"
    with pytest.raises(ValueError, match="Segunda"):
        coletar()


def test_editor_exige_ao_menos_um_dia():
    controle, coletar = _editor_horarios(_Pagina(), None)
    for chk, *_ in _linhas(controle):
        chk.value = False
    with pytest.raises(ValueError, match="ao menos um dia"):
        coletar()
