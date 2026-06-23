from abc import ABC, abstractmethod
from datetime import datetime

from app import db

# --- CLASSES DE ESTADO (State Pattern) ---

class EstadoReserva(ABC):
    """Interface abstrata para os estados da Reserva."""
    
    @abstractmethod
    def confirmar(self, reserva):
        pass

    @abstractmethod
    def cancelar(self, reserva):
        pass

class ReservaPendente(EstadoReserva):
    def confirmar(self, reserva):
        reserva.estado_atual = ReservaConfirmada()
        reserva.status_texto = "Confirmada"
        return "Reserva confirmada com sucesso."

    def cancelar(self, reserva):
        reserva.estado_atual = ReservaCancelada()
        reserva.status_texto = "Cancelada"
        return "Reserva cancelada pelo usuário."

class ReservaConfirmada(EstadoReserva):
    def confirmar(self, reserva):
        raise ValueError("A reserva já está confirmada.")

    def cancelar(self, reserva):
        reserva.estado_atual = ReservaCancelada()
        reserva.status_texto = "Cancelada"
        return "Reserva confirmada foi cancelada. Processar regras de estorno, se houver."

class ReservaCancelada(EstadoReserva):
    def confirmar(self, reserva):
        raise ValueError("Não é possível confirmar uma reserva que já foi cancelada.")

    def cancelar(self, reserva):
        raise ValueError("A reserva já encontra-se cancelada.")

# --- MODELO PRINCIPAL ---

class Reserva(db.Model):
    """Modelo da Reserva no banco de dados."""
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    data_horario = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime)  # término previsto (data_horario + duração)
    status_texto = db.Column(db.String(20), default="Pendente") # Salvo no PostgreSQL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Pagamento (simulado, sem integração bancária real)
    metodo_pagamento = db.Column(db.String(20))   # 'online' | 'presencial'
    status_pagamento = db.Column(db.String(20), default="Pendente")  # Pendente | Pago | Presencial

    # Chaves Estrangeiras
    locatario_id = db.Column(db.Integer, db.ForeignKey('locatarios.id'), nullable=False)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id'), nullable=False)

    def __init__(self, locatario_id, espaco_id, data_horario, data_fim=None):
        self.locatario_id = locatario_id
        self.espaco_id = espaco_id
        self.data_horario = data_horario
        self.data_fim = data_fim
        self.status_texto = "Pendente"
        self.status_pagamento = "Pendente"
        self.created_at = datetime.utcnow()
        self._estado_atual = ReservaPendente() # Inicia sempre como Pendente

    @property
    def estado_atual(self):
        # Lógica para recriar o objeto de Estado baseado no texto do banco ao carregar
        if not hasattr(self, '_estado_atual'):
            if self.status_texto == "Pendente":
                self._estado_atual = ReservaPendente()
            elif self.status_texto == "Confirmada":
                self._estado_atual = ReservaConfirmada()
            elif self.status_texto == "Cancelada":
                self._estado_atual = ReservaCancelada()
        return self._estado_atual

    @estado_atual.setter
    def estado_atual(self, novo_estado):
        self._estado_atual = novo_estado

    # Delegação dos comportamentos para o Estado atual
    def confirmar_reserva(self):
        return self.estado_atual.confirmar(self)

    def cancelar_reserva(self):
        return self.estado_atual.cancelar(self)

    def to_dict(self) -> dict:
        """Serialização padrão consumida pela API/frontend."""
        return {
            "id": self.id,
            "data_horario": self.data_horario.isoformat() if self.data_horario else None,
            "data_fim": self.data_fim.isoformat() if self.data_fim else None,
            "status": self.status_texto,
            "status_pagamento": self.status_pagamento,
            "metodo_pagamento": self.metodo_pagamento,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "locatario_id": self.locatario_id,
            "espaco_id": self.espaco_id,
        }