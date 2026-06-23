from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Usuario(db.Model):
    """Classe abstrata para representar um usuário do sistema."""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(100), nullable= False)
    email = db.Column(db.String(100), unique=True, nullable = False)
    senha = db.Column(db.String(255), nullable = False)
    tipo_usuario = db.Column(db.String(50), nullable = False)  # Campo para diferenciar os tipos de usuários
    ativo = db.Column(db.Boolean, default=True, nullable=False)  # Bloqueio/desbloqueio (admin)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_usuario
    }

    # Prefixos gerados pelo werkzeug; usados para distinguir hash de senha em texto puro (legado).
    _PREFIXOS_HASH = ('pbkdf2:', 'scrypt:', 'argon2')

    def definir_senha(self, senha_pura: str) -> None:
        """Armazena a senha de forma segura (hash werkzeug)."""
        self.senha = generate_password_hash(senha_pura)

    def _senha_e_hash(self) -> bool:
        return bool(self.senha) and self.senha.startswith(self._PREFIXOS_HASH)

    def autenticar(self, senha_informada: str) -> bool:
        """Valida a senha. Migra contas legadas (texto puro) para hash de forma transparente."""
        if not senha_informada or not self.senha:
            return False

        if self._senha_e_hash():
            return check_password_hash(self.senha, senha_informada)

        # Conta legada armazenada em texto puro: compara e, se confere, re-hasheia.
        if self.senha == senha_informada:
            self.definir_senha(senha_informada)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            return True
        return False
    
class Locatario(Usuario):
    """Classe herdada de usuario para representar um locatario/cliente do sistema."""
    __tablename__ = 'locatarios'
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key = True)
    cpf = db.Column(db.String(14), unique=True, nullable = False)
    
    __mapper_args__ = {
        'polymorphic_identity' : 'locatario'
    }

class Locador(Usuario):
    __tablename__ = 'locadores'
    
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key = True)
    cnpj = db.Column(db.String(20), unique=True, nullable = False)
    razao_social = db.Column(db.String(150), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity' : 'locador'
    }
    
class Administrador(Usuario):
    """Classe herdada de usuario para representar um administrador do sistema."""
    __tablename__ = 'administradores'
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key = True)
    
    __mapper_args__ = {
        'polymorphic_identity' : 'administrador'
    }

