"""Comandos de linha de comando (`flask --app main <comando>`)."""

import click

from app import db
from app.factories.usuario_factory import UsuarioFactory
from app.models.usuario_model import Usuario


def registrar_comandos(app):

    @app.cli.command('criar-admin')
    @click.option('--nome', prompt='Nome')
    @click.option('--email', prompt='E-mail')
    @click.option('--senha', prompt='Senha', hide_input=True, confirmation_prompt=True)
    def criar_admin(nome, email, senha):
        """Cria um usuário administrador (necessário para o primeiro acesso)."""
        if Usuario.query.filter_by(email=email).first():
            raise click.ClickException(f"Já existe um usuário com o e-mail {email}.")
        db.session.add(UsuarioFactory.criar_usuario('administrador', nome, email, senha))
        db.session.commit()
        click.echo(f"Administrador '{nome}' criado.")
