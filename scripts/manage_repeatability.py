#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repeatability Limits Management Script

Энэ скрипт нь repeatability (T) limits тохиргоог удирдах, харах, тест хийхэд зориулагдсан.

Хэрэглээ:
    python scripts/manage_repeatability.py --help
    python scripts/manage_repeatability.py --show          # Тохиргоо харах
    python scripts/manage_repeatability.py --test          # Тест ажиллуулах
    python scripts/manage_repeatability.py --summary       # Хураангуй харах
    python scripts/manage_repeatability.py --code Mad      # Тодорхой анализ тест
"""

import sys
import os
from math import inf

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.repeatability import LIMIT_RULES


def show_all_config():
    """Бүх тохиргоог харуулах"""
    print("=" * 80)
    print("REPEATABILITY LIMITS ТОХИРГОО (T - Давтагдах Чадвар)")
    print("=" * 80)
    print()

    print(f"Нийт анализ: {len(LIMIT_RULES)}")
    print()

    # Group by type (single vs bands)
    single_rules = {}
    band_rules = {}

    for code, rule in sorted(LIMIT_RULES.items()):
        if "single" in rule:
            single_rules[code] = rule
        elif "bands" in rule or "bands_detailed" in rule:
            band_rules[code] = rule

    # Display single limit rules
    if single_rules:
        print(f"\n📌 Single Limit Rules ({len(single_rules)} анализ):")
        print("-" * 80)
        for code, rule in sorted(single_rules.items()):
            limit = rule["single"]["limit"]
            mode = rule["single"]["mode"]
            mode_str = "%" if mode == "percent" else "abs"
            print(f"  {code:10s} → T = {limit:6.2f} ({mode_str})")

    # Display band rules
    if band_rules:
        print(f"\n📊 Band Rules ({len(band_rules)} анализ):")
        print("-" * 80)
        for code, rule in sorted(band_rules.items()):
            bands = rule.get("bands_detailed") or rule.get("bands", [])
            print(f"\n  {code}:")
            for i, band in enumerate(bands):
                upper = band["upper"]
                limit = band["limit"]
                mode = band["mode"]
                mode_str = "%" if mode == "percent" else "abs"

                if upper == inf:
                    upper_str = "∞"
                else:
                    upper_str = f"{upper:g}"

                if i == 0:
                    range_str = f"≤ {upper_str}"
                else:
                    prev_upper = bands[i-1]["upper"]
                    if prev_upper == inf:
                        range_str = f"> ∞"
                    else:
                        range_str = f"{prev_upper:g} < x ≤ {upper_str}"

                print(f"    {range_str:20s} → T = {limit:6.3f} ({mode_str})")


def show_summary():
    """Хураангуй мэдээлэл"""
    print("=" * 80)
    print("ХУРААНГУЙ (Summary)")
    print("=" * 80)
    print()

    total = len(LIMIT_RULES)
    single_count = sum(1 for r in LIMIT_RULES.values() if "single" in r)
    band_count = sum(1 for r in LIMIT_RULES.values() if "bands" in r or "bands_detailed" in r)

    print(f"Нийт анализ: {total}")
    print(f"  Single limits: {single_count} анализ")
    print(f"  Band limits: {band_count} анализ")
    print()

    # List all codes
    print("Бүх анализ кодууд:")
    codes = sorted(LIMIT_RULES.keys())
    for i in range(0, len(codes), 6):
        row = codes[i:i+6]
        print("  " + ", ".join(f"{c:10s}" for c in row))


def test_specific_code(code: str):
    """Тодорхой анализын тест"""
    print("=" * 80)
    print(f"ТЕСТ: {code}")
    print("=" * 80)
    print()

    if code not in LIMIT_RULES:
        print(f"❌ '{code}' анализын тохиргоо олдсонгүй!")
        print()
        print("Боломжит кодууд:")
        codes = sorted(LIMIT_RULES.keys())
        for i in range(0, len(codes), 8):
            row = codes[i:i+8]
            print("  " + ", ".join(row))
        return

    rule = LIMIT_RULES[code]

    if "single" in rule:
        limit = rule["single"]["limit"]
        mode = rule["single"]["mode"]
        mode_str = "%" if mode == "percent" else "abs"
        print(f"Төрөл: Single limit")
        print(f"Limit: T = {limit} ({mode_str})")
        print()
        print("Жишээ:")
        test_vals = [0.1, 1.0, 5.0, 10.0]
        for val in test_vals:
            if mode == "percent":
                actual_limit = val * limit / 100
                print(f"  Дундаж = {val:6.2f} → T = {actual_limit:6.3f} ({limit}%)")
            else:
                print(f"  Дундаж = {val:6.2f} → T = {limit:6.3f} (abs)")

    elif "bands" in rule or "bands_detailed" in rule:
        bands = rule.get("bands_detailed") or rule.get("bands", [])
        print(f"Төрөл: Band limits ({len(bands)} bands)")
        print()
        for i, band in enumerate(bands):
            upper = band["upper"]
            limit = band["limit"]
            mode = band["mode"]
            mode_str = "%" if mode == "percent" else "abs"

            if upper == inf:
                upper_str = "∞"
            else:
                upper_str = f"{upper:g}"

            if i == 0:
                range_str = f"≤ {upper_str}"
            else:
                prev_upper = bands[i-1]["upper"]
                range_str = f"{prev_upper:g} < x ≤ {upper_str}"

            print(f"  Band {i+1}: {range_str:20s} → T = {limit} ({mode_str})")

        # Test with sample values
        print()
        print("Жишээ утгууд:")
        test_vals = []
        for band in bands:
            if band["upper"] != inf:
                test_vals.append(band["upper"] - 0.1)
                test_vals.append(band["upper"] + 0.1)
        test_vals = sorted(set(test_vals))[:8]  # Limit to 8 samples

        for val in test_vals:
            # Find applicable band
            for band in bands:
                if val <= band["upper"]:
                    limit = band["limit"]
                    mode = band["mode"]
                    if mode == "percent":
                        actual_limit = val * limit / 100
                        print(f"  Дундаж = {val:6.2f} → T = {actual_limit:6.3f} ({limit}%)")
                    else:
                        print(f"  Дундаж = {val:6.2f} → T = {limit:6.3f} (abs)")
                    break


def run_tests():
    """Автомат тестүүд"""
    print("=" * 80)
    print("ТЕСТҮҮД (Automated Tests)")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # Test 1: All codes have valid structure
    print("Test 1: Бүх анализ зөв бүтэцтэй эсэх")
    for code, rule in LIMIT_RULES.items():
        has_single = "single" in rule
        has_bands = "bands" in rule or "bands_detailed" in rule

        if not (has_single or has_bands):
            print(f"  ❌ {code}: 'single' эсвэл 'bands' байх ёстой")
            failed += 1
        else:
            passed += 1

    print(f"  ✅ {passed}/{passed + failed} анализ зөв бүтэцтэй")
    print()

    # Test 2: Single rules have limit and mode
    print("Test 2: Single rules-үүд limit, mode-тэй эсэх")
    test_passed = 0
    test_failed = 0
    for code, rule in LIMIT_RULES.items():
        if "single" in rule:
            single = rule["single"]
            if "limit" not in single or "mode" not in single:
                print(f"  ❌ {code}: 'limit' болон 'mode' байх ёстой")
                test_failed += 1
            else:
                test_passed += 1

    if test_failed > 0:
        print(f"  ❌ {test_failed} алдаа")
        failed += test_failed
    else:
        print(f"  ✅ {test_passed} single rules бүгд зөв")
        passed += test_passed
    print()

    # Test 3: Band rules have upper, limit, mode
    print("Test 3: Band rules-үүд upper, limit, mode-тэй эсэх")
    test_passed = 0
    test_failed = 0
    for code, rule in LIMIT_RULES.items():
        bands = rule.get("bands") or rule.get("bands_detailed")
        if bands:
            for i, band in enumerate(bands):
                required = {"upper", "limit", "mode"}
                if not required.issubset(set(band.keys())):
                    print(f"  ❌ {code} band {i}: {required} байх ёстой")
                    test_failed += 1
                else:
                    test_passed += 1

    if test_failed > 0:
        print(f"  ❌ {test_failed} алдаа")
        failed += test_failed
    else:
        print(f"  ✅ {test_passed} bands бүгд зөв")
        passed += test_passed
    print()

    # Test 4: Mode values are valid
    print("Test 4: Mode утгууд зөв эсэх (abs эсвэл percent)")
    test_passed = 0
    test_failed = 0
    valid_modes = {"abs", "percent"}

    for code, rule in LIMIT_RULES.items():
        if "single" in rule:
            mode = rule["single"].get("mode")
            if mode not in valid_modes:
                print(f"  ❌ {code}: mode '{mode}' буруу (abs/percent байх ёстой)")
                test_failed += 1
            else:
                test_passed += 1

        bands = rule.get("bands") or rule.get("bands_detailed")
        if bands:
            for i, band in enumerate(bands):
                mode = band.get("mode")
                if mode not in valid_modes:
                    print(f"  ❌ {code} band {i}: mode '{mode}' буруу")
                    test_failed += 1
                else:
                    test_passed += 1

    if test_failed > 0:
        print(f"  ❌ {test_failed} алдаа")
        failed += test_failed
    else:
        print(f"  ✅ {test_passed} mode утга зөв")
        passed += test_passed
    print()

    # Summary
    print("=" * 80)
    print(f"Үр дүн: {passed} давсан, {failed} амжилтгүй")
    if failed > 0:
        print("❌ Зарим тест амжилтгүй боллоо!")
        return 1
    else:
        print("✅ Бүх тест амжилттай!")
        return 0


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Repeatability Limits Management Tool"
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Бүх тохиргоог харуулах'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Хураангуй мэдээлэл'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Тест ажиллуулах'
    )
    parser.add_argument(
        '--code',
        type=str,
        help='Тодорхой анализ тест хийх (жнь: Mad, Aad, P)'
    )

    args = parser.parse_args()

    # Default: show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    # Execute commands
    if args.show:
        show_all_config()

    if args.summary:
        show_summary()

    if args.test:
        return run_tests()

    if args.code:
        test_specific_code(args.code)

    return 0


if __name__ == '__main__':
    sys.exit(main())
