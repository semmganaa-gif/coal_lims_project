#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display Precision Management Script

Энэ скрипт нь тоон оронгийн тохиргоог удирдах, харах, тест хийхэд зориулагдсан.

Хэрэглээ:
    python scripts/manage_precision.py --help
    python scripts/manage_precision.py --show          # Тохиргоо харах
    python scripts/manage_precision.py --test          # Тест ажиллуулах
    python scripts/manage_precision.py --summary       # Хураангуй харах
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.display_precision import (
    DECIMAL_PLACES,
    DEFAULT_DECIMAL_PLACES,
    get_decimal_places,
    format_result,
    get_precision_summary,
    PRECISION_GROUPS,
)


def show_all_config():
    """Бүх тохиргоог харуулах"""
    print("=" * 80)
    print("ТООН ОРОНГИЙН ТОХИРГОО (Display Precision Configuration)")
    print("=" * 80)
    print()

    print(f"Default precision: {DEFAULT_DECIMAL_PLACES} орон")
    print(f"Total analysis codes: {len(DECIMAL_PLACES)}")
    print()

    # Group by precision
    by_precision = {}
    for code, places in sorted(DECIMAL_PLACES.items()):
        if places not in by_precision:
            by_precision[places] = []
        by_precision[places].append(code)

    # Display grouped
    for places in sorted(by_precision.keys()):
        codes = by_precision[places]
        print(f"\n{places} орон ({len(codes)} анализ):")
        print("-" * 80)

        # Print in columns
        codes_sorted = sorted(codes)
        for i in range(0, len(codes_sorted), 5):
            row = codes_sorted[i:i+5]
            print("  " + ", ".join(f"{c:12s}" for c in row))

    print()


def show_summary():
    """Хураангуй мэдээлэл"""
    summary = get_precision_summary()

    print("=" * 80)
    print("ХУРААНГУЙ (Summary)")
    print("=" * 80)
    print()

    print(f"Нийт анализ: {summary['total_codes']}")
    print(f"Default: {summary['default_precision']} орон")
    print()

    print("Бүлгээр:")
    for precision, codes in sorted(summary['by_precision'].items()):
        print(f"  {precision} орон: {len(codes)} анализ")

    print()
    print("Групп тохиргоо:")
    for group_name, group_info in PRECISION_GROUPS.items():
        print(f"\n  {group_info['name']}:")
        print(f"    Жишээ: {group_info['example']}")
        print(f"    Тоо: {len(group_info['codes'])} анализ")


def run_tests():
    """Тест ажиллуулах"""
    print("=" * 80)
    print("ТЕСТҮҮД (Tests)")
    print("=" * 80)
    print()

    test_cases = [
        # (value, code, expected_result)
        (10.256, "Aad", "10.26"),
        (10.251, "Aad", "10.25"),
        (0.0156, "P", "0.016"),
        (0.0154, "P", "0.015"),
        (25432.8, "CV", "25433"),
        (25432.3, "CV", "25432"),
        (5.55, "CSN", "5.5"),
        (5.51, "CSN", "5.5"),
        (75.123, "Gi", "75"),
        (None, "Aad", "-"),
        (10.5, None, "10.50"),  # Default 2 decimals
        (10.5, "UNKNOWN", "10.50"),  # Unknown code, default
    ]

    passed = 0
    failed = 0

    for value, code, expected in test_cases:
        result = format_result(value, code)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1
        else:
            failed += 1

        code_str = f"'{code}'" if code else "None"
        print(f"{status} format_result({value}, {code_str:10s}) = '{result}' "
              f"(expected: '{expected}')")

    print()
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("\n❌ Some tests failed!")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


def test_specific_code(code: str, value: float = None):
    """Тодорхой анализын тест"""
    print("=" * 80)
    print(f"ТЕСТ: {code}")
    print("=" * 80)
    print()

    decimal_places = get_decimal_places(code)
    print(f"Тоон орон: {decimal_places}")
    print()

    if value is None:
        # Test with sample values
        test_values = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 0.0156, 25432.8]
    else:
        test_values = [value]

    print("Жишээ үр дүнгүүд:")
    for val in test_values:
        formatted = format_result(val, code)
        print(f"  {val:10.4f} → {formatted}")


def interactive_mode():
    """Интерактив горим"""
    print("=" * 80)
    print("ИНТЕРАКТИВ ГОРИМ")
    print("=" * 80)
    print("'quit' эсвэл 'exit' гэж бичээд гарах")
    print()

    while True:
        try:
            # Get analysis code
            code = input("\nАнализын код (жнь: Aad, P, CV): ").strip()
            if code.lower() in ('quit', 'exit', 'q'):
                break

            if not code:
                continue

            # Get value
            value_str = input("Үр дүнгийн утга (жнь: 10.256): ").strip()
            if value_str.lower() in ('quit', 'exit', 'q'):
                break

            try:
                value = float(value_str)
            except ValueError:
                print(f"❌ Буруу тоо: {value_str}")
                continue

            # Format and display
            decimal_places = get_decimal_places(code)
            formatted = format_result(value, code)

            print(f"\n📊 Үр дүн:")
            print(f"  Анализ: {code}")
            print(f"  Тоон орон: {decimal_places}")
            print(f"  Оруулсан: {value}")
            print(f"  Харуулах: {formatted}")

        except KeyboardInterrupt:
            print("\n\nInterrupted")
            break
        except Exception as e:
            print(f"❌ Алдаа: {e}")

    print("\nBye!")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Display Precision Management Tool"
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
        help='Тодорхой анализ тест хийх (жнь: Aad)'
    )
    parser.add_argument(
        '--value',
        type=float,
        help='Тест хийх утга (--code-той хамт)'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Интерактив горим'
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
        test_specific_code(args.code, args.value)

    if args.interactive:
        interactive_mode()

    return 0


if __name__ == '__main__':
    sys.exit(main())
