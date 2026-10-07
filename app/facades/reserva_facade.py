"""Fachada das operações de reserva.

Único ponto de contato das rotas com a lógica de agendamento: validação de
disponibilidade, conflito de horário, reserva duplicada, pagamento (simulado)
e cancelamento — sempre via o padrão State da `Reserva`.
"""

import uuid
from datetime import timedelta

from app.models.reserva_model import Reserva
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.services import agenda, avaliacoes, precos, validacao
from app import db


class ReservaFacade:

    @staticmethod
    def _espaco_reservavel(espaco_id):
        espaco = EspacoEsportivo.query.get(espaco_id) if espaco_id else None
        if not espaco or not espaco.ativo or not espaco.disponivel:
            raise ValueError("Espaço esportivo não encontrado ou indisponível.")
        return espaco

    @staticmethod
    def _verificar_periodo(locatario_id, espaco, inicio, fim):
        """Levanta ValueError (com o motivo) se este cliente não pode reservar o período.

        As mesmas regras valem para a reserva avulsa e para cada data de uma série.
        """
        if inicio < validacao.agora():
            raise ValueError("A data/horário da reserva deve estar no futuro.")
        if not espaco.atende(inicio, fim):
            raise ValueError("Este espaço não atende neste horário. "
                             + espaco.descricao_funcionamento(inicio.weekday()))
        if agenda.esta_bloqueado(espaco.id, inicio, fim):
            raise ValueError("Horário indisponível: bloqueado pelo proprietário do espaço.")

        # Reserva duplicada (mesmo cliente, espaço e horário ainda ativa).
        duplicada = Reserva.query.filter(
            Reserva.locatario_id == locatario_id,
            Reserva.espaco_id == espaco.id,
            Reserva.data_horario == inicio,
            Reserva.status_texto.in_(("Pendente", "Confirmada")),
        ).first()
        if duplicada:
            raise ValueError("Você já possui uma reserva para este espaço neste horário.")

        # Conflito com reserva confirmada de qualquer cliente.
        if agenda.esta_reservado(espaco.id, inicio, fim):
            raise ValueError("Já existe uma reserva confirmada para este horário.")

    @staticmethod
    def _validar_metodo(espaco, metodo_pagamento) -> str:
        metodo = (metodo_pagamento or "").strip().lower()
        if metodo not in ("online", "presencial"):
            raise ValueError("Método de pagamento inválido (use 'online' ou 'presencial').")
        if espaco:
            if metodo == "online" and not espaco.aceita_online:
                raise ValueError("Este espaço não aceita pagamento online.")
            if metodo == "presencial" and not espaco.aceita_presencial:
                raise ValueError("Este espaço não aceita pagamento presencial.")
        return metodo

    @staticmethod
    def _ocorrencias(data_horario, data_fim, semanas):
        """[(inicio, fim), ...] — o mesmo dia e horário, uma vez por semana."""
        semanas = validacao.validar_semanas(semanas)
        inicio = validacao.parse_datetime(data_horario)
        fim = validacao.parse_datetime(data_fim) if data_fim else inicio + agenda.DURACAO_SLOT
        if fim <= inicio:
            raise ValueError("O horário de término deve ser depois do início.")
        return [(inicio + timedelta(weeks=n), fim + timedelta(weeks=n)) for n in range(semanas)]

    @staticmethod
    def previa_serie(locatario_id, espaco_id, data_horario, data_fim, semanas) -> list:
        """Cada data da série com disponibilidade, motivo (se indisponível) e preço. Não reserva nada."""
        espaco = ReservaFacade._espaco_reservavel(espaco_id)
        datas = []
        for inicio, fim in ReservaFacade._ocorrencias(data_horario, data_fim, semanas):
            try:
                ReservaFacade._verificar_periodo(locatario_id, espaco, inicio, fim)
                motivo = None
            except ValueError as e:
                motivo = str(e)
            datas.append({"inicio": inicio.isoformat(), "fim": fim.isoformat(),
                          "disponivel": motivo is None, "motivo": motivo,
                          "preco": precos.preco_do_periodo(espaco, inicio, fim)})
        return datas

    @staticmethod
    def realizar_serie(locatario_id, espaco_id, data_horario, data_fim, semanas, metodo_pagamento):
        """Reserva recorrente (mensalista): confirma as datas livres e devolve as que ficaram de fora.

        Retorna (reservas_criadas, recusadas, serie_id); `recusadas` traz início e motivo.
        Se nenhuma data estiver livre, nada é gravado.
        """
        espaco = ReservaFacade._espaco_reservavel(espaco_id)
        metodo = ReservaFacade._validar_metodo(espaco, metodo_pagamento)
        serie_id = str(uuid.uuid4())
        criadas, recusadas = [], []
        for inicio, fim in ReservaFacade._ocorrencias(data_horario, data_fim, semanas):
            try:
                ReservaFacade._verificar_periodo(locatario_id, espaco, inicio, fim)
            except ValueError as e:
                recusadas.append({"inicio": inicio.isoformat(), "motivo": str(e)})
                continue
            reserva = Reserva(locatario_id=locatario_id, espaco_id=espaco.id, data_horario=inicio,
                              data_fim=fim, serie_id=serie_id,
                              valor_total=precos.preco_do_periodo(espaco, inicio, fim))
            reserva.confirmar_reserva()  # padrão State; a série já nasce confirmada
            reserva.metodo_pagamento = metodo
            reserva.status_pagamento = "Pago" if metodo == "online" else "Presencial"
            db.session.add(reserva)
            criadas.append(reserva)
        if not criadas:
            db.session.rollback()
            return [], recusadas, None
        db.session.commit()
        return criadas, recusadas, serie_id

    @staticmethod
    def cancelar_serie(serie_id) -> int:
        """Cancela as reservas da série que ainda não terminaram; devolve quantas foram canceladas."""
        agora = validacao.agora()
        canceladas = 0
        for reserva in Reserva.query.filter_by(serie_id=serie_id).all():
            if reserva.status_texto in ("Pendente", "Confirmada") and reserva.fim_efetivo > agora:
                reserva.cancelar_reserva()  # padrão State
                canceladas += 1
        db.session.commit()
        return canceladas

    @staticmethod
    def realizar_reserva(locatario_id, espaco_id, data_horario, data_fim=None):
        if not locatario_id or not espaco_id:
            raise ValueError("Locatário e espaço são obrigatórios.")

        inicio = validacao.validar_data_horario_futuro(data_horario)
        fim = validacao.parse_datetime(data_fim) if data_fim else inicio + agenda.DURACAO_SLOT
        if fim <= inicio:
            raise ValueError("O horário de término deve ser depois do início.")

        espaco = ReservaFacade._espaco_reservavel(espaco_id)
        ReservaFacade._verificar_periodo(locatario_id, espaco, inicio, fim)

        nova_reserva = Reserva(
            locatario_id=locatario_id,
            espaco_id=espaco_id,
            data_horario=inicio,
            data_fim=fim,
            valor_total=precos.preco_do_periodo(espaco, inicio, fim),
        )
        db.session.add(nova_reserva)
        db.session.commit()
        return nova_reserva

    @staticmethod
    def confirmar_pagamento_e_reserva(reserva_id, metodo_pagamento):
        """Confirma a reserva registrando o método de pagamento (simulado)."""
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            raise ValueError("Reserva não encontrada.")

        metodo = ReservaFacade._validar_metodo(EspacoEsportivo.query.get(reserva.espaco_id), metodo_pagamento)

        # Reconfere conflito no momento da confirmação.
        fim = reserva.data_fim or (reserva.data_horario + agenda.DURACAO_SLOT)
        if agenda.esta_reservado(reserva.espaco_id, reserva.data_horario, fim,
                                 ignorar_reserva_id=reserva.id):
            raise ValueError("Horário já foi confirmado por outra reserva.")

        try:
            mensagem = reserva.confirmar_reserva()  # padrão State
            reserva.metodo_pagamento = metodo
            reserva.status_pagamento = "Pago" if metodo == "online" else "Presencial"
            db.session.commit()
            return mensagem
        except ValueError:
            db.session.rollback()
            raise

    @staticmethod
    def registrar_comparecimento(reserva_id, compareceu: bool):
        """Depois do horário, registra se o cliente compareceu (Concluída) ou faltou (no-show)."""
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            raise ValueError("Reserva não encontrada.")
        if reserva.fim_efetivo > validacao.agora():
            raise ValueError("Só é possível registrar o comparecimento depois do horário da reserva.")
        try:
            mensagem = reserva.registrar_comparecimento(compareceu)  # padrão State
            if not compareceu:
                avaliacoes.remover_da_reserva(reserva.id)  # só avalia quem compareceu
            db.session.commit()
            return mensagem
        except ValueError:
            db.session.rollback()
            raise

    @staticmethod
    def cancelar_reserva(reserva_id):
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            raise ValueError("Reserva não encontrada.")
        try:
            mensagem = reserva.cancelar_reserva()  # padrão State
            db.session.commit()
            return mensagem
        except ValueError:
            db.session.rollback()
            raise
