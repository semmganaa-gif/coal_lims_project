# run.py

import os
from app import create_app, db, socketio
from app.models import User, Sample

# CLI commands нь bootstrap_app(app) → init_cli(app) дотроос автомат бүртгэгдэнэ
app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sample': Sample}

if __name__ == '__main__':
    # ✅ ЗАСВАРЛАСАН: Debug mode зөвхөн development орчинд
    is_debug = os.getenv('FLASK_ENV', 'production') == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    # 🔐 SSL/HTTPS тохиргоо (Web Serial API-д шаардлагатай)
    ssl_cert = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
    ssl_key = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')

    # SSL файлууд байвал HTTPS ашиглана
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print("🔐 HTTPS идэвхтэй (SSL certificate олдлоо)")
        print(f"🌐 https://{host}:{port}")
        ssl_context = (ssl_cert, ssl_key)
    else:
        print("⚠️  SSL certificate олдсонгүй - HTTP ашиглаж байна")
        print(f"🌐 http://{host}:{port}")
        print("")
        print("   HTTPS идэвхжүүлэхийн тулд:")
        print("   python generate_ssl.py")
        print("")
        ssl_context = None

    # SocketIO-той сервер эхлүүлэх (WebSocket дэмжлэгтэй)
    socketio.run(
        app,
        debug=is_debug,
        host=host,
        port=port,
        ssl_context=ssl_context
    )
