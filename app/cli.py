# app/cli.py

from app import db
from app.models import User
import click

def register_commands(app):
    @app.cli.group()
    def users():
        """Хэрэглэгчийн удирдлагын командууд."""
        pass

    @users.command()
    @click.argument('username')
    @click.argument('password')
    @click.argument('role')
    def create(username, password, role):
        """Шинэ хэрэглэгч үүсгэнэ.

        ROLE: beltgegch, himich, ahlah, admin
        """
        if User.query.filter_by(username=username).first():
            click.echo(f"'{username}' нэртэй хэрэглэгч аль хэдийн байна.")
            return

        if role not in ['beltgegch', 'himich', 'ahlah', 'admin']:
            click.echo("Алдаа: Эрх буруу байна. 'beltgegch', 'himich', 'ahlah', 'admin' гэсэн утгуудын аль нэгийг сонгоно уу.")
            return

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"'{username}' нэртэй, '{role}' эрхтэй хэрэглэгчийг амжилттай үүсгэлээ.")
