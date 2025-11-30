#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Requirements.txt Verification Script

Энэ скрипт нь:
1. Бүх шаардлагатай packages суусан эсэхийг шалгана
2. Version conflicts шалгана
3. Дутуу packages мэдээлнэ
"""

import sys
import importlib
import pkg_resources

# Шаардлагатай packages
REQUIRED_PACKAGES = {
    'flask': '3.1.2',
    'flask_sqlalchemy': '3.1.1',
    'flask_migrate': '4.1.0',
    'flask_login': '0.6.3',
    'flask_wtf': '1.2.1',
    'flask_mail': '0.10.0',
    'flask_limiter': '3.5.0',
    'sqlalchemy': '2.0.44',
    'alembic': '1.17.1',
    'wtforms': '3.1.2',
    'pandas': '2.1.4',
    'numpy': '1.26.4',
    'openpyxl': '3.1.2',
    'python-dateutil': '2.8.2',
    'pytz': '2024.1',
    'python-dotenv': '1.2.1',
}

# Package нэр mapping (import name != package name)
IMPORT_NAME_MAP = {
    'flask_sqlalchemy': 'flask_sqlalchemy',
    'flask_migrate': 'flask_migrate',
    'flask_login': 'flask_login',
    'flask_wtf': 'flask_wtf',
    'flask_mail': 'flask_mail',
    'flask_limiter': 'flask_limiter',
    'python-dateutil': 'dateutil',
    'python-dotenv': 'dotenv',
}


def check_package(package_name, expected_version=None):
    """
    Package суусан эсэх шалгах

    Returns:
        tuple: (installed, version, status_message)
    """
    # Import name авах
    import_name = IMPORT_NAME_MAP.get(package_name, package_name.replace('-', '_'))

    try:
        # Try to import
        mod = importlib.import_module(import_name)

        # Try to get version
        try:
            # Try package_resources first
            installed_version = pkg_resources.get_distribution(package_name).version
        except:
            # Try __version__ attribute
            installed_version = getattr(mod, '__version__', 'unknown')

        # Version check
        if expected_version and installed_version != expected_version:
            status = f"⚠️  Version mismatch: {installed_version} (expected {expected_version})"
        else:
            status = f"✅ OK (v{installed_version})"

        return True, installed_version, status

    except ImportError as e:
        return False, None, f"❌ NOT INSTALLED - {str(e)}"


def main():
    """Main verification"""
    print("=" * 70)
    print("Coal LIMS - Requirements Verification")
    print("=" * 70)
    print()

    missing = []
    warnings = []
    ok = []

    for package, version in REQUIRED_PACKAGES.items():
        print(f"Checking {package}...", end=" ")
        installed, inst_version, status = check_package(package, version)
        print(status)

        if not installed:
            missing.append(package)
        elif "⚠️" in status:
            warnings.append((package, inst_version, version))
        else:
            ok.append(package)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ OK: {len(ok)}/{len(REQUIRED_PACKAGES)}")
    print(f"⚠️  Warnings: {len(warnings)}")
    print(f"❌ Missing: {len(missing)}")
    print()

    if missing:
        print("❌ MISSING PACKAGES:")
        for pkg in missing:
            print(f"   - {pkg}")
        print()
        print("Install them:")
        print(f"   pip install {' '.join(missing)}")
        print()

    if warnings:
        print("⚠️  VERSION MISMATCHES:")
        for pkg, installed, expected in warnings:
            print(f"   - {pkg}: {installed} (expected {expected})")
        print()

    if not missing and not warnings:
        print("🎉 All packages installed correctly!")
        print()
        return 0
    else:
        print("⚠️  Some issues found. Please fix them.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
