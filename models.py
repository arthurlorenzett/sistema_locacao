from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Associação N:N entre Reserva e ItemExtra
reserva_item_assoc = db.Table('reserva_item_assoc',
    db.Column('reserva_id', db.Integer, db.ForeignKey('reserva.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item_extra.id'))
)

# --- INÍCIO: Classes de Entidade (Estrutura e Herança) ---

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20))

    # Configuração de Herança no SQLAlchemy (Joined Table Inheritance)
    __mapper_args__ = {
        'polymorphic_on': tipo_usuario,
        'polymorphic_identity': 'usuario'
    }

    def autenticar(self, senha_input):
        return self.senha == senha_input

class Locatario(Usuario):
    __tablename__ = 'locatario'
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'locatario'}
    
    reservas = db.relationship('Reserva', backref='locatario', lazy=True)

class Locador(Usuario):
    __tablename__ = 'locador'
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'locador'}
    
    cnpj = db.Column(db.String(18), unique=True)
    razao_social = db.Column(db.String(100))
    quadras = db.relationship('Quadra', backref='locador', lazy=True)

class Quadra(db.Model):
    __tablename__ = 'quadra'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_esporte = db.Column(db.String(50), nullable=False)
    preco_hora = db.Column(db.Numeric(10, 2), nullable=False)
    disponivel = db.Column(db.Boolean, default=True)
    
    locador_id = db.Column(db.Integer, db.ForeignKey('locador.id'), nullable=False)
    reservas = db.relationship('Reserva', backref='quadra', lazy=True)

class ItemExtra(db.Model):
    __tablename__ = 'item_extra'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)

class Pagamento(db.Model):
    __tablename__ = 'pagamento'
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pagamento = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='PENDENTE')
    
    reserva_id = db.Column(db.Integer, db.ForeignKey('reserva.id'), nullable=False)

# --- FIM: Classes de Entidade ---

# --- INÍCIO: Padrão Comportamental State ---
class EstadoReserva:
    def processar_pagamento(self, reserva):
        raise NotImplementedError
    def cancelar_reserva(self, reserva):
        raise NotImplementedError

class EstadoPendente(EstadoReserva):
    def processar_pagamento(self, reserva):
        reserva.status_db = 'CONFIRMADA'
    def cancelar_reserva(self, reserva):
        reserva.status_db = 'CANCELADA'

class EstadoConfirmada(EstadoReserva):
    def processar_pagamento(self, reserva):
        raise ValueError("A reserva já está confirmada e paga.")
    def cancelar_reserva(self, reserva):
        reserva.status_db = 'CANCELADA'
        # Aqui entraria a lógica de aplicar ou não estorno

class EstadoCancelada(EstadoReserva):
    def processar_pagamento(self, reserva):
        raise ValueError("Não é possível pagar uma reserva cancelada.")
    def cancelar_reserva(self, reserva):
        raise ValueError("A reserva já se encontra cancelada.")
# --- FIM: Padrão Comportamental State ---

class Reserva(db.Model):
    __tablename__ = 'reserva'
    id = db.Column(db.Integer, primary_key=True)
    data_reserva = db.Column(db.Date, nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    valor_base = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    status_db = db.Column(db.String(20), default='PENDENTE', nullable=False)
    
    locatario_id = db.Column(db.Integer, db.ForeignKey('locatario.id'), nullable=False)
    quadra_id = db.Column(db.Integer, db.ForeignKey('quadra.id'), nullable=False)
    
    pagamento = db.relationship('Pagamento', backref='reserva', uselist=False, lazy=True)
    itens_extras = db.relationship('ItemExtra', secondary=reserva_item_assoc, lazy='subquery', backref=db.backref('reservas', lazy=True))

    @property
    def estado_atual(self):
        estados = {
            'PENDENTE': EstadoPendente(),
            'CONFIRMADA': EstadoConfirmada(),
            'CANCELADA': EstadoCancelada()
        }
        return estados.get(self.status_db.upper(), EstadoPendente())

    def alterar_estado_pagamento(self):
        self.estado_atual.processar_pagamento(self)

    def cancelar(self):
        self.estado_atual.cancelar_reserva(self)