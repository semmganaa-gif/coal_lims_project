# -*- coding: utf-8 -*-
"""
Production server - Waitress

Ашиглах:
    python run_production.py

Тохиргоо:
    - Host: 0.0.0.0 (бүх IP-аас холбогдох боломжтой)
    - Port: 5000 (эсвэл PORT environment variable)
    - Threads: 4 (эсвэл WEB_CONCURRENCY environment variable)
"""
import os
from waitress import serve
from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    threads = int(os.environ.get('WEB_CONCURRENCY', 4))

    print(f"""
============================================================
Coal LIMS Production Server
============================================================
Host:    {host}
Port:    {port}
Threads: {threads}
URL:     http://localhost:{port}
============================================================
    """)

    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        url_scheme='http',
        ident='Coal LIMS'
    )
