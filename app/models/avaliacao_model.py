from datetime import datetime

from app import db


class Avaliacao(db.Model):
    """Nota (1 a 5) e comentário que o locatário deixa depois de uma reserva realizada."""
    __tablename__ = 'avaliacoes'

    id = db.Column(db.Integer, primary_key=True)
    # Uma avaliação por reserva.
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id', ondelete='CASCADE'),
                           nullable=False, unique=True)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    locatario_id = db.Column(db.Integer, db.ForeignKey('locatarios.id', ondelete='CASCADE'), nullable=False)
    nota = db.Column(db.SmallInteger, nullable=False)
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def resumo(self) -> dict:
        """Forma curta anexada à reserva (o que o cliente escreveu)."""
        return {"nota": self.nota, "comentario": self.comentario}
