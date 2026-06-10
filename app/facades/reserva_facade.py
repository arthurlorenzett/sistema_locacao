from app.models.reserva_model import Reserva
from app.models.espacoEsportivo_model import EspacoEsportivo
from app import db

class ReservaFacade:
    """
    Fachada para simplificar as operações complexas de agendamento.
    Serve como único ponto de contato para o frontend/rotas.
    """
    
    @staticmethod
    def realizar_reserva(locatario_id, espaco_id, data_horario):
        # 1. Verifica se o espaço existe e está disponível
        espaco = EspacoEsportivo.query.get(espaco_id)
        if not espaco or not espaco.disponivel:
            raise ValueError("Espaço esportivo não encontrado ou indisponível.")
            
        # 2. Verifica choque de horários (simplificado para o exemplo)
        reserva_existente = Reserva.query.filter_by(
            espaco_id=espaco_id, 
            data_horario=data_horario,
            status_texto="Confirmada"
        ).first()
        
        if reserva_existente:
            raise ValueError("Já existe uma reserva confirmada para este horário.")
            
        # 3. Cria a nova reserva (Nasce com o status 'Pendente' via padrão State)
        nova_reserva = Reserva(
            locatario_id=locatario_id,
            espaco_id=espaco_id,
            data_horario=data_horario
        )
        
        # 4. Salva no banco de dados PostgreSQL
        db.session.add(nova_reserva)
        db.session.commit()
        
        return nova_reserva

    @staticmethod
    def confirmar_pagamento_e_reserva(reserva_id, metodo_pagamento):
        """
        O sistema registrará a intenção de pagamento e o método escolhido, mudando 
        o status da reserva no banco de dados.
        """
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            raise ValueError("Reserva não encontrada.")
            
        try:
            # O padrão State garante que a transição ocorra corretamente
            mensagem = reserva.confirmar_reserva() 
            
            # Registra como foi pago (texto simples para prestação de contas)
            registro_pagamento = f"Pago via {metodo_pagamento}" 
            
            db.session.commit()
            return f"{mensagem} {registro_pagamento}"
            
        except ValueError as e:
            # Captura erros do Padrão State (ex: tentar confirmar algo já cancelado)
            db.session.rollback()
            raise e