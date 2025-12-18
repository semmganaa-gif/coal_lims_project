# -*- coding: utf-8 -*-
"""
HTTPS Development Server

Web Serial API ашиглахад HTTPS шаардлагатай.
Энэ script нь self-signed certificate ашиглан HTTPS server ажиллуулна.

Ашиглах:
    1. SSL certificate үүсгэх:
       python scripts/generate_ssl_cert.py

    2. HTTPS server ажиллуулах:
       python run_https.py

    3. Browser-т нээх:
       https://localhost:5443

Анхааруулга:
    - Self-signed certificate тул browser warning гарна
    - Chrome: "Advanced" -> "Proceed to localhost (unsafe)"
    - Firefox: "Advanced" -> "Accept the Risk and Continue"
"""

import os
import ssl
from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('HTTPS_PORT', 5443))

    cert_file = 'ssl/cert.pem'
    key_file = 'ssl/key.pem'

    # Certificate байгаа эсэхийг шалгах
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("""
❌ SSL Certificate олдсонгүй!

Эхлээд certificate үүсгэнэ үү:
    python scripts/generate_ssl_cert.py
""")
        exit(1)

    # SSL context үүсгэх
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)

    print(f"""
============================================================
Coal LIMS HTTPS Development Server
============================================================
Host:    {host}
Port:    {port}
URL:     https://localhost:{port}
============================================================

⚠️  Self-signed certificate тул browser warning гарна!
    "Advanced" -> "Proceed to localhost (unsafe)" дарна уу.

🔌 Web Serial API (жин холбох) ажиллахад бэлэн.
============================================================
    """)

    # Flask development server HTTPS-тэй ажиллуулах
    app.run(
        host=host,
        port=port,
        ssl_context=ssl_context,
        debug=False,
        threaded=True
    )
