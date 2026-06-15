import pytest
from app.factories.usuario_factory import UsuarioFactory
from app.models.usuario_model import Locatario

def test_criar_locatario_com_sucesso():
    """Testa a criação de um locatário com todos os dados corretos."""
    usuario = UsuarioFactory.criar_usuario(
        tipo='locatario',
        nome='João Silva',
        email='joao@email.com',
        senha='123',
        cpf='111.222.333-44'
    )
    assert isinstance(usuario, Locatario)
    assert usuario.nome == 'João Silva'
    assert usuario.cpf == '111.222.333-44'

def test_criar_locatario_sem_cpf_deve_falhar():
    """Testa a regra de negócio: Locatário não pode ser criado sem CPF."""
    # O pytest.raises verifica se o sistema atirou o erro corretamente
    with pytest.raises(ValueError, match="Locatário requer CPF"):
        UsuarioFactory.criar_usuario(
            tipo='locatario',
            nome='Maria',
            email='maria@email.com',
            senha='123'
            # CPF omitido propositadamente
        )

def test_criar_locador_sem_cnpj_deve_falhar():
    """Testa a regra de negócio: Locador precisa de CNPJ e Razão Social."""
    with pytest.raises(ValueError, match="Locador requer CNPJ e Razão Social"):
        UsuarioFactory.criar_usuario(
            tipo='locador',
            nome='Empresa X',
            email='contato@empresax.com',
            senha='123',
            cnpj='' # CNPJ vazio
        )