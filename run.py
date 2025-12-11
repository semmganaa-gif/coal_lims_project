# run.py

import os
from app import create_app, db, socketio
from app.models import User, Sample
from app.cli import register_commands

app = create_app()
register_commands(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sample': Sample}

if __name__ == '__main__':
    # ✅ ЗАСВАРЛАСАН: Debug mode зөвхөн development орчинд
    is_debug = os.getenv('FLASK_ENV', 'production') == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    # SocketIO-той сервер эхлүүлэх (WebSocket дэмжлэгтэй)
    socketio.run(app, debug=is_debug, host=host, port=port)
