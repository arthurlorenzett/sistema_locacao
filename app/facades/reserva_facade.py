"""Fachada das operações de reserva.

Único ponto de contato das rotas com a lógica de agendamento: validação de
disponibilidade, conflito de horário, reserva duplicada, pagamento (simulado)
e cancelamento — sempre via o padrão State da `Reserva`.
"""

from app.models.reserva_model import Reserva
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.services import agenda, avaliacoes, precos, validacao
from app import db


class ReservaFacade:

    @staticmethod
    def realizar_reserva(locatario_id, espaco_id, data_horario, data_fim=None):
        if not locatario_id or not espaco_id:
            raise ValueError("Locatário e espaço são obrigatórios.")

        inicio = validacao.validar_data_horario_futuro(data_horario)
        fim = validacao.parse_datetime(data_fim) if data_fim else inicio + agenda.DURACAO_SLOT
        if fim <= inicio:
            raise ValueError("O horário de término deve ser depois do início.")

        espaco = EspacoEsportivo.query.get(espaco_id)
        if not espaco or not espaco.ativo or not espaco.disponivel:
            raise ValueError("Espaço esportivo não encontrado ou indisponível.")
        if not espaco.atende(inicio, fim):
            raise ValueError("Este espaço não atende neste horário. "
                             + espaco.descricao_funcionamento(inicio.weekday()))
        if agenda.esta_bloqueado(espaco_id, inicio, fim):
            raise ValueError("Horário indisponível: bloqueado pelo proprietário do espaço.")

        # Reserva duplicada (mesmo cliente, espaço e horário ainda ativa).
        duplicada = Reserva.query.filter(
            Reserva.locatario_id == locatario_id,
            Reserva.espaco_id == espaco_id,
            Reserva.data_horario == inicio,
            Reserva.status_texto.in_(("Pendente", "Confirmada")),
        ).first()
        if duplicada:
            raise ValueError("Você já possui uma reserva para este espaço neste horário.")

        # Conflito com reserva confirmada de qualquer cliente.
        if agenda.esta_reservado(espaco_id, inicio, fim):
            raise ValueError("Já existe uma reserva confirmada para este horário.")

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

        metodo = (metodo_pagamento or "").strip().lower()
        if metodo not in ("online", "presencial"):
            raise ValueError("Método de pagamento inválido (use 'online' ou 'presencial').")

        espaco = EspacoEsportivo.query.get(reserva.espaco_id)
        if espaco:
            if metodo == "online" and not espaco.aceita_online:
                raise ValueError("Este espaço não aceita pagamento online.")
            if metodo == "presencial" and not espaco.aceita_presencial:
                raise ValueError("Este espaço não aceita pagamento presencial.")

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
