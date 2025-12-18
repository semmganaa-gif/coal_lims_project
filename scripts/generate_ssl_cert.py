# scripts/generate_ssl_cert.py
# -*- coding: utf-8 -*-
"""
Self-signed SSL certificate үүсгэх

Web Serial API ашиглахад HTTPS шаардлагатай.
Энэ script нь development/testing-д ашиглах self-signed certificate үүсгэнэ.

Ашиглах:
    python scripts/generate_ssl_cert.py

Үүссэн файлууд:
    ssl/cert.pem  - Certificate
    ssl/key.pem   - Private key
"""

import os
import subprocess
import sys


def generate_certificate():
    """OpenSSL ашиглан self-signed certificate үүсгэх"""

    ssl_dir = 'ssl'
    cert_file = os.path.join(ssl_dir, 'cert.pem')
    key_file = os.path.join(ssl_dir, 'key.pem')

    # SSL directory үүсгэх
    os.makedirs(ssl_dir, exist_ok=True)

    # Certificate байгаа эсэхийг шалгах
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"⚠️  Certificate аль хэдийн байна:")
        print(f"   {cert_file}")
        print(f"   {key_file}")
        response = input("Дахин үүсгэх үү? (y/N): ")
        if response.lower() != 'y':
            print("Цуцлагдлаа.")
            return

    # OpenSSL команд
    cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:4096',
        '-keyout', key_file,
        '-out', cert_file,
        '-days', '365',
        '-nodes',  # No password
        '-subj', '/CN=localhost/O=Coal LIMS/C=MN'
    ]

    print("🔐 Self-signed SSL certificate үүсгэж байна...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"OpenSSL алдаа: {result.stderr}")

        print(f"""
✅ SSL Certificate амжилттай үүслээ!

Файлууд:
  Certificate: {cert_file}
  Private Key: {key_file}

HTTPS server ажиллуулах:
  python run_https.py

Анхааруулга:
  - Энэ нь self-signed certificate тул browser warning гарна
  - Production-д Let's Encrypt эсвэл бодит certificate ашиглах хэрэгтэй
""")

    except FileNotFoundError:
        print("""
❌ OpenSSL олдсонгүй!

Windows дээр OpenSSL суулгах:
  1. https://slproweb.com/products/Win32OpenSSL.html -с татах
  2. Суулгаад PATH-д нэмэх

Эсвэл Python-оор үүсгэх:
  pip install pyOpenSSL
  python scripts/generate_ssl_cert_python.py
""")
        return create_cert_python(cert_file, key_file)


def create_cert_python(cert_file, key_file):
    """pyOpenSSL ашиглан certificate үүсгэх"""
    try:
        from OpenSSL import crypto
    except ImportError:
        print("pyOpenSSL суулгаж байна...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyOpenSSL'])
        from OpenSSL import crypto

    # Key pair үүсгэх
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    # Certificate үүсгэх
    cert = crypto.X509()
    cert.get_subject().C = "MN"
    cert.get_subject().O = "Coal LIMS"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 жил
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Файлд хадгалах
    ssl_dir = os.path.dirname(cert_file)
    os.makedirs(ssl_dir, exist_ok=True)

    with open(cert_file, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_file, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    print(f"""
✅ SSL Certificate амжилттай үүслээ! (pyOpenSSL)

Файлууд:
  Certificate: {cert_file}
  Private Key: {key_file}
""")


if __name__ == '__main__':
    generate_certificate()
