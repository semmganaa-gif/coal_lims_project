# run.py

from app import create_app, db
from app.models import User, Sample
from app.cli import register_commands # Энэ мөр байгаа эсэх

app = create_app()
register_commands(app) # ЭНЭ МӨР ЧУХАЛ! app = create_app() -ийн ДОР байх ёстой

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sample': Sample}
