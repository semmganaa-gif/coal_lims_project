#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Төслийн бүтцийн асуудлуудыг шинжлэх
"""

import os
import ast
from collections import defaultdict

def analyze_file(filepath):
    """Файлын функцүүд, классуудыг шинжлэх"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
                else:
                    for alias in node.names:
                        imports.append(f"import {alias.name}")

        return {
            'functions': functions,
            'classes': classes,
            'imports': imports
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 80)
    print("ТӨСЛИЙН БҮТЦИЙН ШИНЖИЛГЭЭ / PROJECT STRUCTURE ANALYSIS")
    print("=" * 80)

    # 1. HELPERS файлууд
    print("\n1. HELPERS ФАЙЛУУДЫН АГУУЛГА:")
    print("-" * 80)

    helper_files = [
        'app/routes/analysis/helpers.py',
        'app/routes/api/helpers.py',
        'app/routes/main/helpers.py',
        'app/utils/shift_helper.py'
    ]

    for filepath in helper_files:
        if os.path.exists(filepath):
            info = analyze_file(filepath)
            print(f"\n📁 {filepath}")
            print(f"   Functions: {', '.join(info.get('functions', []))}")
            if info.get('classes'):
                print(f"   Classes: {', '.join(info['classes'])}")

    # 2. AUDIT файлууд
    print("\n\n2. AUDIT ФАЙЛУУДЫН АГУУЛГА:")
    print("-" * 80)

    audit_files = [
        'app/routes/audit_log_service.py',
        'app/utils/audit.py',
        'app/routes/api/audit_api.py'
    ]

    for filepath in audit_files:
        if os.path.exists(filepath):
            info = analyze_file(filepath)
            print(f"\n📁 {filepath}")
            print(f"   Functions: {', '.join(info.get('functions', []))}")
            if info.get('classes'):
                print(f"   Classes: {', '.join(info['classes'])}")

    # 3. Давхардал шалгах
    print("\n\n3. ДАВХАРДСАН ФУНКЦҮҮД:")
    print("-" * 80)

    all_functions = defaultdict(list)

    for root, dirs, files in os.walk('app'):
        if '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                info = analyze_file(filepath)
                for func in info.get('functions', []):
                    all_functions[func].append(filepath)

    # Давхардсан функцүүдыг хэвлэх
    duplicates = {k: v for k, v in all_functions.items() if len(v) > 1}

    if duplicates:
        for func, files in sorted(duplicates.items()):
            if not func.startswith('_'):  # Private функцүүдийг алгасах
                print(f"\n⚠️  {func}:")
                for f in files:
                    print(f"     - {f}")
    else:
        print("✅ Давхардсан функц олдсонгүй")

    # 4. Config файлууд
    print("\n\n4. CONFIG ФАЙЛУУД:")
    print("-" * 80)

    config_files = []
    for root, dirs, files in os.walk('app/config'):
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                config_files.append(filepath)

    for filepath in sorted(config_files):
        info = analyze_file(filepath)
        size = os.path.getsize(filepath)
        print(f"\n📁 {filepath} ({size} bytes)")
        funcs = info.get('functions', [])
        if funcs:
            print(f"   Functions: {', '.join(funcs)}")
        classes = info.get('classes', [])
        if classes:
            print(f"   Classes: {', '.join(classes)}")

    # 5. Utils файлууд
    print("\n\n5. UTILS ФАЙЛУУД:")
    print("-" * 80)

    util_files = []
    for f in os.listdir('app/utils'):
        if f.endswith('.py') and f != '__init__.py':
            filepath = os.path.join('app/utils', f)
            util_files.append(filepath)

    for filepath in sorted(util_files):
        info = analyze_file(filepath)
        size = os.path.getsize(filepath)
        func_count = len(info.get('functions', []))
        print(f"{filepath:50s} {size:7d} bytes  {func_count:3d} functions")

if __name__ == '__main__':
    main()
