#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест файлуудыг нэгтгэх script
"""
import os
import re
from pathlib import Path
from collections import defaultdict

TESTS_DIR = Path(__file__).parent.parent / "tests"
INTEGRATION_DIR = TESTS_DIR / "integration"
UNIT_DIR = TESTS_DIR / "unit"
MERGED_DIR = TESTS_DIR / "merged"

# Нэгтгэх категориуд
INTEGRATION_CATEGORIES = {
    'admin': ['admin'],
    'analysis': ['analysis'],
    'api': ['api'],
    'quality': ['quality', 'capa', 'proficiency', 'complaints', 'environmental'],
    'report': ['report', 'consumption'],
    'index': ['index', 'main', 'routes_logic', 'page'],
    'equipment': ['equipment'],
    'import': ['import'],
    'chat': ['chat'],
    'qc': ['qc', 'control_charts', 'westgard'],
    'kpi': ['kpi'],
    'settings': ['settings'],
    'auth': ['auth', 'csrf'],
    'workflow': ['workflow', 'full'],
    'notification': ['notification'],
    'samples': ['samples'],
    'senior': ['senior'],
    'workspace': ['workspace'],
}

UNIT_CATEGORIES = {
    'utils': ['utils', 'normalize', 'sorting', 'shifts', 'codes', 'datetime', 'audit', 'conversions', 'converters', 'database', 'exports', 'parameters', 'security', 'settings'],
    'models': ['models'],
    'validators': ['validators'],
    'westgard': ['westgard'],
    'calculations': ['calculations', 'server'],
    'license': ['license', 'hardware', 'fingerprint'],
    'notifications': ['notifications'],
    'services': ['services'],
    'schemas': ['schemas'],
    'cli': ['cli'],
    'decorators': ['decorators'],
    'qc': ['qc'],
}


def get_category(filename: str, categories: dict) -> str:
    """Файлын категорийг олох"""
    name = filename.lower().replace('test_', '').replace('.py', '')
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in name:
                return cat
    return 'other'


def extract_imports(content: str) -> set:
    """Import мөрүүдийг задлах"""
    imports = set()
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            imports.add(line)
    return imports


def extract_classes_and_functions(content: str) -> str:
    """Import-ууд болон docstring-үүдийг хасаж class/function-уудыг авах"""
    lines = content.split('\n')
    result = []
    skip_imports = True
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip file-level docstring
        if i < 5 and (stripped.startswith('"""') or stripped.startswith("'''")):
            if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                continue
            in_docstring = not in_docstring
            docstring_char = stripped[:3]
            continue

        if in_docstring:
            if docstring_char and docstring_char in stripped:
                in_docstring = False
            continue

        # Skip imports
        if skip_imports:
            if stripped.startswith('import ') or stripped.startswith('from '):
                continue
            if stripped == '' and not result:
                continue
            skip_imports = False

        result.append(line)

    return '\n'.join(result)


def merge_files(source_dir: Path, categories: dict, output_dir: Path, prefix: str):
    """Файлуудыг нэгтгэх"""
    output_dir.mkdir(exist_ok=True)

    # Категориор бүлэглэх
    grouped = defaultdict(list)

    for f in source_dir.glob("test_*.py"):
        if f.name == '__init__.py':
            continue
        cat = get_category(f.name, categories)
        grouped[cat].append(f)

    # Нэгтгэх
    for cat, files in grouped.items():
        if not files:
            continue

        all_imports = set()
        all_content = []

        all_imports.add("import pytest")
        all_imports.add("from datetime import datetime, timedelta")
        all_imports.add("from unittest.mock import patch, MagicMock")

        for f in sorted(files):
            content = f.read_text(encoding='utf-8', errors='ignore')

            # Import-үүдийг цуглуулах
            imports = extract_imports(content)
            all_imports.update(imports)

            # Class/function-уудыг авах
            body = extract_classes_and_functions(content)
            if body.strip():
                all_content.append(f"\n# === FROM: {f.name} ===\n")
                all_content.append(body)

        # Эцсийн файл бичих
        output_file = output_dir / f"test_{prefix}_{cat}.py"

        # Import-үүдийг эрэмбэлэх
        std_imports = []
        third_imports = []
        local_imports = []

        for imp in sorted(all_imports):
            if imp.startswith('from app') or imp.startswith('import app'):
                local_imports.append(imp)
            elif imp.startswith('from ') and not any(x in imp for x in ['flask', 'sqlalchemy', 'pytest', 'unittest']):
                if 'datetime' in imp or 'collections' in imp or 'io' in imp or 'json' in imp:
                    std_imports.append(imp)
                else:
                    third_imports.append(imp)
            elif 'flask' in imp or 'sqlalchemy' in imp or 'pytest' in imp or 'unittest' in imp:
                third_imports.append(imp)
            else:
                std_imports.append(imp)

        final_content = f'''# tests/merged/test_{prefix}_{cat}.py
"""
{cat.upper()} тестүүд - Нэгтгэсэн
Үүсгэсэн: {os.popen("date /t").read().strip() if os.name == 'nt' else "auto"}
"""
'''
        if std_imports:
            final_content += '\n'.join(sorted(set(std_imports))) + '\n'
        if third_imports:
            final_content += '\n'.join(sorted(set(third_imports))) + '\n'
        if local_imports:
            final_content += '\n'.join(sorted(set(local_imports))) + '\n'

        final_content += '\n'.join(all_content)

        output_file.write_text(final_content, encoding='utf-8')
        print(f"✅ {output_file.name}: {len(files)} файл нэгтгэсэн")


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=== Merging test files ===\n")

    print("Integration tests:")
    merge_files(INTEGRATION_DIR, INTEGRATION_CATEGORIES, MERGED_DIR, "int")

    print("\nUnit tests:")
    merge_files(UNIT_DIR, UNIT_CATEGORIES, MERGED_DIR, "unit")

    print(f"\nDone! Merged files: {MERGED_DIR}")
    print(f"\nCheck: pytest {MERGED_DIR} -v")


if __name__ == "__main__":
    main()
