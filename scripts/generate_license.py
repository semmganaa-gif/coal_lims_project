# -*- coding: utf-8 -*-
"""
License Generator - LIMS лиценз үүсгэх скрипт

ЗӨВХӨН ТА АШИГЛАНА!
Энэ скриптийг үйлчлүүлэгчид ӨГЧ БОЛОХГҮЙ!

Хэрэглээ:
    python generate_license.py

Жишээ:
    Компани: Эрдэнэс Тавантолгой
    Хугацаа: 2025-12-31
    Hardware ID: (үйлчлүүлэгчээс авна)
"""
import hashlib
import json
import base64
import os
import sys
from datetime import datetime, timedelta

# =====================================================
# НУУЦ ТҮЛХҮҮРҮҮД - license_protection.py дотортой ижил байх ёстой!
# =====================================================
LICENSE_SECRET_KEY = "ТАНЫ_НУУЦ_ТҮЛХҮҮР_ЭНД_32_ТЭМДЭГТ"
LICENSE_SALT = "COAL_LIMS_2024_LICENSE_SALT_V1"
SIGNATURE_KEY = "ТАНЫ_ГАРЫН_ҮСГИЙН_ТҮЛХҮҮР_ЭНД"


def _create_signature(data: dict) -> str:
    """Лицензийн гарын үсэг үүсгэх"""
    sign_data = f"{data.get('company', '')}{data.get('expiry', '')}{data.get('hardware_id', '')}{SIGNATURE_KEY}"
    return hashlib.sha256(sign_data.encode()).hexdigest()[:32]


def generate_license(
    company: str,
    expiry_date: str,
    hardware_id: str = None,
    company_code: str = "",
    max_users: int = 10,
    max_samples: int = 10000,
    is_trial: bool = False
) -> str:
    """
    Лиценз түлхүүр үүсгэх

    Args:
        company: Компанийн нэр
        expiry_date: Дуусах огноо (YYYY-MM-DD)
        hardware_id: Hardware ID (заавал биш)
        company_code: Компанийн код
        max_users: Хамгийн их хэрэглэгчийн тоо
        max_samples: Сарын хамгийн их дээжийн тоо
        is_trial: Туршилтын лиценз эсэх

    Returns:
        Base64 encoded license key
    """
    data = {
        'company': company,
        'company_code': company_code,
        'expiry': expiry_date,
        'issued': datetime.utcnow().isoformat(),
        'hardware_id': hardware_id,
        'max_users': max_users,
        'max_samples': max_samples,
        'is_trial': is_trial,
        'version': '1.0'
    }

    # Гарын үсэг нэмэх
    data['signature'] = _create_signature(data)

    # JSON -> Base64
    json_str = json.dumps(data, ensure_ascii=False)
    encoded = base64.b64encode(json_str.encode()).decode()

    return encoded


def generate_trial_license(company: str, days: int = 30) -> str:
    """Туршилтын лиценз үүсгэх"""
    expiry = (datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d')
    return generate_license(
        company=company,
        expiry_date=expiry,
        max_users=5,
        max_samples=1000,
        is_trial=True
    )


def interactive_mode():
    """Интерактив горимд лиценз үүсгэх"""
    print("=" * 60)
    print("  COAL LIMS - ЛИЦЕНЗ ҮҮСГЭГЧ")
    print("=" * 60)
    print()

    # Компанийн мэдээлэл
    company = input("Компанийн нэр: ").strip()
    if not company:
        print("АЛДАА: Компанийн нэр оруулна уу!")
        return

    company_code = input("Компанийн код (заавал биш): ").strip()

    # Хугацаа
    print("\nХугацаа сонгох:")
    print("  1. 1 жил")
    print("  2. 2 жил")
    print("  3. Өөрөө оруулах")
    print("  4. 30 хоногийн туршилт")

    choice = input("Сонголт (1-4): ").strip()

    if choice == "1":
        expiry = (datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d')
        is_trial = False
    elif choice == "2":
        expiry = (datetime.utcnow() + timedelta(days=730)).strftime('%Y-%m-%d')
        is_trial = False
    elif choice == "3":
        expiry = input("Дуусах огноо (YYYY-MM-DD): ").strip()
        is_trial = False
    elif choice == "4":
        expiry = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
        is_trial = True
    else:
        print("АЛДАА: Буруу сонголт!")
        return

    # Hardware ID
    print("\nHardware ID:")
    print("  (Үйлчлүүлэгчийн /license/hardware-id хаягаас авна)")
    print("  (Хоосон үлдээвэл ямар ч компьютерт ажиллана)")
    hardware_id = input("Hardware ID: ").strip() or None

    # Хязгаарлалт
    try:
        max_users = int(input("\nХэрэглэгчийн тоо (default: 10): ").strip() or "10")
    except ValueError:
        max_users = 10

    try:
        max_samples = int(input("Сарын дээжийн тоо (default: 10000): ").strip() or "10000")
    except ValueError:
        max_samples = 10000

    # Лиценз үүсгэх
    print("\n" + "=" * 60)
    print("ЛИЦЕНЗ ҮҮСГЭЖ БАЙНА...")
    print("=" * 60)

    license_key = generate_license(
        company=company,
        expiry_date=expiry,
        hardware_id=hardware_id,
        company_code=company_code,
        max_users=max_users,
        max_samples=max_samples,
        is_trial=is_trial
    )

    print("\n" + "=" * 60)
    print("ЛИЦЕНЗ АМЖИЛТТАЙ ҮҮСЛЭЭ!")
    print("=" * 60)
    print(f"\nКомпани: {company}")
    print(f"Дуусах огноо: {expiry}")
    print(f"Hardware ID: {hardware_id or 'Ямар ч компьютер'}")
    print(f"Хэрэглэгч: {max_users}")
    print(f"Туршилт: {'Тийм' if is_trial else 'Үгүй'}")

    print("\n" + "-" * 60)
    print("ЛИЦЕНЗ ТҮЛХҮҮР:")
    print("-" * 60)
    print(license_key)
    print("-" * 60)

    # Файлд хадгалах
    filename = f"license_{company.replace(' ', '_')}_{expiry}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Coal LIMS License\n")
        f.write(f"=" * 40 + "\n")
        f.write(f"Компани: {company}\n")
        f.write(f"Дуусах огноо: {expiry}\n")
        f.write(f"Hardware ID: {hardware_id or 'Any'}\n")
        f.write(f"Хэрэглэгч: {max_users}\n")
        f.write(f"Туршилт: {'Yes' if is_trial else 'No'}\n")
        f.write(f"=" * 40 + "\n\n")
        f.write("LICENSE KEY:\n")
        f.write(license_key)

    print(f"\nФайлд хадгалагдлаа: {filename}")


def main():
    if len(sys.argv) > 1:
        # Command line arguments
        if sys.argv[1] == "--trial":
            company = sys.argv[2] if len(sys.argv) > 2 else "Test Company"
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            license_key = generate_trial_license(company, days)
            print(license_key)
        else:
            print("Usage:")
            print("  python generate_license.py           # Interactive mode")
            print("  python generate_license.py --trial 'Company' 30")
    else:
        interactive_mode()


if __name__ == '__main__':
    main()
