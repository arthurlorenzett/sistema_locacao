from app import db


class RegraPreco(db.Model):
    """Preço por hora diferente do padrão numa faixa de horário de um dia da semana.

    Como nos horários de funcionamento, `inicio`/`fim` são minutos desde a
    meia-noite (fim até 1440) e `dia_semana` vai de 0 (segunda) a 6 (domingo).
    Fora das regras vale o `preco_hora` do espaço.
    """
    __tablename__ = 'regras_preco'

    id = db.Column(db.Integer, primary_key=True)
    espaco_id = db.Column(db.Integer, db.ForeignKey('espacos_esportivos.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    dia_semana = db.Column(db.SmallInteger, nullable=False)
    inicio = db.Column(db.SmallInteger, nullable=False)
    fim = db.Column(db.SmallInteger, nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
