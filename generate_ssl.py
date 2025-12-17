#!/usr/bin/env python
"""
SSL Certificate Generator for Coal LIMS
Дотоод сүлжээнд ашиглах self-signed certificate үүсгэнэ.

Ажиллуулах:
    python generate_ssl.py

Үүсэх файлууд:
    ssl/cert.pem  - Certificate
    ssl/key.pem   - Private key
"""

import os
import subprocess
import sys
from datetime import datetime

def generate_ssl_certificate():
    """Self-signed SSL certificate үүсгэх"""

    ssl_dir = os.path.join(os.path.dirname(__file__), 'ssl')
    cert_file = os.path.join(ssl_dir, 'cert.pem')
    key_file = os.path.join(ssl_dir, 'key.pem')

    # SSL folder үүсгэх
    if not os.path.exists(ssl_dir):
        os.makedirs(ssl_dir)
        print(f"✅ SSL folder үүсгэлээ: {ssl_dir}")

    # Хэрэв certificate байвал шалгах
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"⚠️  SSL certificate аль хэдийн байна:")
        print(f"    Certificate: {cert_file}")
        print(f"    Private Key: {key_file}")

        response = input("Шинээр үүсгэх үү? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Цуцаллаа.")
            return False

    # OpenSSL шалгах
    try:
        subprocess.run(['openssl', 'version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL суулгаагүй байна!")
        print("")
        print("Windows дээр суулгах:")
        print("  1. https://slproweb.com/products/Win32OpenSSL.html")
        print("  2. Win64 OpenSSL Light татаж суулгана")
        print("  3. PATH-д нэмнэ: C:\\Program Files\\OpenSSL-Win64\\bin")
        return False

    print("🔐 SSL Certificate үүсгэж байна...")

    # Certificate үүсгэх команд
    cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:4096',
        '-keyout', key_file,
        '-out', cert_file,
        '-days', '365',
        '-nodes',
        '-subj', '/CN=Coal LIMS/O=Laboratory/C=MN'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("")
            print("✅ SSL Certificate амжилттай үүслээ!")
            print("")
            print(f"   Certificate: {cert_file}")
            print(f"   Private Key: {key_file}")
            print(f"   Хүчинтэй хугацаа: 365 хоног")
            print("")
            print("🚀 Сервер эхлүүлэх:")
            print("   python run.py")
            print("")
            print("🌐 Хандах URL:")
            print("   https://192.168.1.100:5000")
            print("")
            print("⚠️  Анхааруулга:")
            print("   Хөтөч 'Not Secure' гэж анхааруулах болно.")
            print("   'Advanced' → 'Proceed' дарж үргэлжлүүлнэ.")
            return True
        else:
            print(f"❌ Алдаа гарлаа: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Алдаа: {e}")
        return False


if __name__ == '__main__':
    generate_ssl_certificate()
