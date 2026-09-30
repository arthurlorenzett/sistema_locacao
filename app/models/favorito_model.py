from datetime import datetime

from app import db


class Favorito(db.Model):
    """Espaço esportivo marcado como favorito por um locatário."""
    __tablename__ = 'favoritos'
    __table_args__ = (
        db.UniqueConstraint('locatario_id', 'espaco_id', name='uq_favorito_locatario_espaco'),
    )

    id = db.Column(db.Integer, primary_key=True)
    locatario_id = db.Column(db.Integer, db.ForeignKey('locatarios.id', ondelete='CASCADE'), nullable=False)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
