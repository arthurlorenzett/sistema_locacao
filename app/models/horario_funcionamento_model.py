from app import db
from app.services.validacao import formatar_hora

DIAS_SEMANA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


class HorarioFuncionamento(db.Model):
    """Horário em que um espaço atende num dia da semana (0 = segunda ... 6 = domingo).

    Os horários são guardados em minutos desde a meia-noite; `fechamento` pode ser
    1440 (24:00), para espaços que funcionam até a meia-noite.
    """
    __tablename__ = 'horarios_funcionamento'
    __table_args__ = (
        db.UniqueConstraint('espaco_id', 'dia_semana', name='uq_horario_espaco_dia'),
    )

    id = db.Column(db.Integer, primary_key=True)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id', ondelete='CASCADE'), nullable=False)
    dia_semana = db.Column(db.SmallInteger, nullable=False)
    abertura = db.Column(db.SmallInteger, nullable=False)
    fechamento = db.Column(db.SmallInteger, nullable=False)

    def to_dict(self) -> dict:
        return {
            "dia_semana": self.dia_semana,
            "abre": formatar_hora(self.abertura),
            "fecha": formatar_hora(self.fechamento),
        }
