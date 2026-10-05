"""Preços dinâmicos: quanto custa um período num espaço, conforme as regras por dia/horário.

Fora das regras vale o preço padrão do espaço. O período é dividido nos limites
das regras e cada trecho é cobrado proporcionalmente ao seu preço por hora.
"""

from datetime import datetime, time, timedelta

from app.services.validacao import formatar_hora

_FIM_DO_DIA = 24 * 60


def preco_do_periodo(espaco, inicio: datetime, fim: datetime) -> float:
    total, cursor = 0.0, inicio
    while cursor < fim:
        meia_noite = datetime.combine(cursor.date(), time())
        minuto = (cursor - meia_noite) // timedelta(minutes=1)
        do_dia = sorted((r for r in espaco.regras_preco if r.dia_semana == cursor.weekday()),
                        key=lambda r: r.inicio)

        regra = next((r for r in do_dia if r.inicio <= minuto < r.fim), None)
        if regra:
            limite, preco = regra.fim, regra.preco_hora
        else:
            # Preço padrão até começar a próxima regra do dia (ou até a meia-noite).
            limite = next((r.inicio for r in do_dia if r.inicio > minuto), _FIM_DO_DIA)
            preco = espaco.preco_hora

        fim_do_trecho = min(fim, meia_noite + timedelta(minutes=limite))
        total += (fim_do_trecho - cursor) / timedelta(hours=1) * preco
        cursor = fim_do_trecho
    return round(total, 2)


def faixa(espaco) -> tuple:
    """(menor, maior) preço por hora praticado pelo espaço, contando as regras."""
    valores = [espaco.preco_hora] + [r.preco_hora for r in espaco.regras_preco]
    return min(valores), max(valores)


def agrupar(regras) -> list:
    """Junta as linhas por dia em regras como o locador cadastrou.

    [{"dias": [5, 6], "inicio": "18:00", "fim": "23:00", "preco_hora": 180.0}, ...]
    """
    grupos = {}
    for r in regras:
        grupos.setdefault((r.inicio, r.fim, r.preco_hora), []).append(r.dia_semana)
    itens = [{"dias": sorted(dias), "inicio": formatar_hora(ini), "fim": formatar_hora(fim), "preco_hora": preco}
             for (ini, fim, preco), dias in grupos.items()]
    return sorted(itens, key=lambda g: (g["dias"], g["inicio"]))
