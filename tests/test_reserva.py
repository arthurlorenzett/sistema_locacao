import pytest
from app.models.reserva_model import Reserva, ReservaConfirmada

def test_reserva_nasce_pendente():
    """Regra: Toda a reserva deve iniciar no estado Pendente."""
    reserva = Reserva(locatario_id=1, espaco_id=1, data_horario="2026-10-10 10:00")
    assert reserva.status_texto == "Pendente"

def test_confirmar_reserva_pendente():
    """Regra: Uma reserva pendente pode ser confirmada."""
    reserva = Reserva(locatario_id=1, espaco_id=1, data_horario="2026-10-10 10:00")
    
    # Executa a ação de confirmar
    mensagem = reserva.confirmar_reserva()
    
    # Verifica se a transição de estado ocorreu corretamente
    assert reserva.status_texto == "Confirmada"
    assert isinstance(reserva.estado_atual, ReservaConfirmada)

def test_nao_pode_confirmar_reserva_cancelada():
    """Regra de Segurança: Não se pode confirmar o que já foi cancelado."""
    reserva = Reserva(locatario_id=1, espaco_id=1, data_horario="2026-10-10 10:00")
    
    # Cancela a reserva primeiro
    reserva.cancelar_reserva() 
    
    # Tenta confirmar e espera que o sistema bloqueie com um erro
    with pytest.raises(ValueError, match="Não é possível confirmar uma reserva que já foi cancelada"):
        reserva.confirmar_reserva()