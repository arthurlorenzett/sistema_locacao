from app import db

class EspacoEsportivo(db.Model):
    """
    Classe para representar um espaço esportivo (quadra, campo, etc).
    """
    __tablename__ = 'espacos_esportivos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_esporte = db.Column(db.String(50), nullable=False)   # modalidade (Futsal, Tênis, Vôlei...)
    preco_hora = db.Column(db.Float, nullable=False)
    disponivel = db.Column(db.Boolean, default=True)

    # Campos de catálogo/busca
    regiao = db.Column(db.String(100))
    tipo_quadra = db.Column(db.String(50))     # ex.: Society, Saibro, Coberta
    descricao = db.Column(db.Text)
    endereco = db.Column(db.String(200))
    foto_url = db.Column(db.String(500))

    # Métodos de pagamento aceitos pelo proprietário
    aceita_online = db.Column(db.Boolean, default=True, nullable=False)
    aceita_presencial = db.Column(db.Boolean, default=True, nullable=False)

    # Ativo/bloqueado (desativação pelo dono ou bloqueio pelo admin)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    locador_id = db.Column(db.Integer, db.ForeignKey('locadores.id'), nullable=False)
    # chave estrangeira para associar o espaço esportivo ao locador que o possui

    def to_dict(self) -> dict:
        """Serialização padrão consumida pela API/frontend."""
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo_esporte": self.tipo_esporte,
            "modalidade": self.tipo_esporte,
            "preco_hora": self.preco_hora,
            "disponivel": self.disponivel,
            "regiao": self.regiao,
            "tipo_quadra": self.tipo_quadra,
            "descricao": self.descricao,
            "endereco": self.endereco,
            "foto_url": self.foto_url,
            "aceita_online": self.aceita_online,
            "aceita_presencial": self.aceita_presencial,
            "ativo": self.ativo,
            "locador_id": self.locador_id,
        }