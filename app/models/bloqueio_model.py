from datetime import datetime

from app import db


class Bloqueio(db.Model):
    """Período em que o locador fechou a agenda do espaço (manutenção, evento privado...)."""
    __tablename__ = 'bloqueios'

    id = db.Column(db.Integer, primary_key=True)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200))  # visível só para o locador
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "espaco_id": self.espaco_id,
            "inicio": self.inicio.isoformat(),
            "fim": self.fim.isoformat(),
            "motivo": self.motivo,
        }
