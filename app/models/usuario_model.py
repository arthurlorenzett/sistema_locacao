from app import db

class Usuario(db.Model):
    """Classe abstrata para representar um usuário do sistema."""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(100), nullable= False)
    email = db.Column(db.String(100), unique=True, nullable = False)
    senha = db.Column(db.String(255), nullable = False)
    tipo_usuario = db.Column(db.String(50), nullable = False)  # Campo para diferenciar os tipos de usuários
    
    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_usuario
    }
    
    def autenticar(self, senha_informada):
        if self.senha == senha_informada:
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

class UsuarioFactory:
    """Fábrica responsavel por instanciar diferentes tipos de usuários. Implementa Factory Method."""
    
    @staticmethod
    def criar_usuario (tipo, nome, email, senha, **kwargs):
        if tipo == 'locatario':
            return Locatario(nome=nome, email=email, senha=senha)
        
        elif tipo == 'locador':
            cnpj = kwargs.get('cnpj')
            razao_social = kwargs.get('razao_social')
            if not cnpj or not razao_social:
                raise ValueError("Locador requer CNPJ e Rrazão Social")
            return Locador(nome=nome, email=email, senha=senha, cnpj=cnpj, razao_social=razao_social)
        
        elif tipo == 'administrador':
            return Administrador(nome=nome, email=email, senha=senha)
        
        else:
            raise ValueError("Tipo de usuário '{tipo}' desconhecido")