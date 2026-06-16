from app import db

class EspacoEsportivo(db.Model):
    """
    Classe para representar um espaço esportivo (quadra, campo, etc).
    """
    __tablename__ = 'espacos_esportivos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_esporte = db.Column(db.String(50), nullable=False)
    preco_hora = db.Column(db.Float, nullable=False)
    disponivel = db.Column(db.Boolean, default=True)
    
    locador_id = db.Column(db.Integer, db.ForeignKey('locadores.id'), nullable=False)
#chave estrangeira para associar o espaço esportivo ao locador que o possui