"""Fachada das operações de reserva.

Único ponto de contato das rotas com a lógica de agendamento: validação de
disponibilidade, conflito de horário, reserva duplicada, pagamento (simulado)
e cancelamento — sempre via o padrão State da `Reserva`.
"""

from datetime import timedelta

from app.models.reserva_model import Reserva
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.services import validacao
from app import db

# Duração padrão de uma reserva quando não há data_fim explícita.
_SLOT_PADRAO = timedelta(hours=1)


class ReservaFacade:

    @staticmethod
    def _ha_sobreposicao(espaco_id, inicio, fim, ignorar_id=None) -> bool:
        """Detecta choque de horário com reservas confirmadas (intervalos abertos à direita)."""
        confirmadas = Reserva.query.filter_by(espaco_id=espaco_id, status_texto="Confirmada").all()
        for r in confirmadas:
            if ignorar_id and r.id == ignorar_id:
                continue
            r_fim = r.data_fim or (r.data_horario + _SLOT_PADRAO)
            if inicio < r_fim and r.data_horario < fim:
                return True
        return False

    @staticmethod
    def realizar_reserva(locatario_id, espaco_id, data_horario, data_fim=None):
        if not locatario_id or not espaco_id:
            raise ValueError("Locatário e espaço são obrigatórios.")

        inicio = validacao.validar_data_horario_futuro(data_horario)
        fim = validacao.parse_datetime(data_fim) if data_fim else inicio + _SLOT_PADRAO
        if fim <= inicio:
            raise ValueError("O horário de término deve ser depois do início.")

        espaco = EspacoEsportivo.query.get(espaco_id)
        if not espaco or not espaco.ativo or not espaco.disponivel:
            raise ValueError("Espaço esportivo não encontrado ou indisponível.")

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
        if ReservaFacade._ha_sobreposicao(espaco_id, inicio, fim):
            raise ValueError("Já existe uma reserva confirmada para este horário.")

        nova_reserva = Reserva(
            locatario_id=locatario_id,
            espaco_id=espaco_id,
            data_horario=inicio,
            data_fim=fim,
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
        fim = reserva.data_fim or (reserva.data_horario + _SLOT_PADRAO)
        if ReservaFacade._ha_sobreposicao(reserva.espaco_id, reserva.data_horario, fim,
                                          ignorar_id=reserva.id):
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
