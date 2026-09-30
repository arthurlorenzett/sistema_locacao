from datetime import datetime, time, timedelta

from app import db
from app.models.horario_funcionamento_model import DIAS_SEMANA, HorarioFuncionamento

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

    # Grade semanal de funcionamento (vazia = espaço antigo, sem restrição de horário)
    horarios = db.relationship(HorarioFuncionamento, lazy='selectin', cascade='all, delete-orphan',
                               order_by=HorarioFuncionamento.dia_semana)

    def horario_do_dia(self, dia_semana):
        return next((h for h in self.horarios if h.dia_semana == dia_semana), None)

    def atende(self, inicio: datetime, fim: datetime) -> bool:
        """True se o período [inicio, fim) cabe no horário de funcionamento do dia."""
        if not self.horarios:
            return True
        h = self.horario_do_dia(inicio.weekday())
        if not h:
            return False
        # Minutos contados a partir da meia-noite do dia de início: terminar à
        # meia-noite seguinte dá 1440 (24:00) e qualquer coisa além não cabe.
        meia_noite = datetime.combine(inicio.date(), time())
        ini_min = (inicio - meia_noite) // timedelta(minutes=1)
        fim_min = (fim - meia_noite) // timedelta(minutes=1)
        return h.abertura <= ini_min and fim_min <= h.fechamento

    def descricao_funcionamento(self, dia_semana) -> str:
        h = self.horario_do_dia(dia_semana)
        if not h:
            return f"O espaço fica fechado neste dia ({DIAS_SEMANA[dia_semana]})."
        d = h.to_dict()
        return f"Funcionamento ({DIAS_SEMANA[dia_semana]}): {d['abre']}–{d['fecha']}."

    def definir_horarios(self, grade):
        """Substitui a grade semanal; `grade` vem de validacao.validar_horarios."""
        self.horarios.clear()
        # Remove os antigos antes de inserir: a unique (espaco, dia) não aceita os dois juntos.
        db.session.flush()
        self.horarios.extend(HorarioFuncionamento(dia_semana=d, abertura=a, fechamento=f)
                             for d, a, f in grade)

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
            "horarios": [h.to_dict() for h in self.horarios],
        }