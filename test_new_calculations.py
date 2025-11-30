#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for newly added server-side calculations: CV, Gi, FM, Solid, TRD

Энэ скрипт нь 5 шинэ тооцоололыг туршина.
"""

import sys
sys.path.insert(0, '.')

from app.utils.server_calculations import (
    calc_calorific_value_cv,
    calc_gray_king_gi,
    calc_free_moisture_fm,
    calc_solid,
    calc_trd,
    verify_and_recalculate
)


def test_cv():
    """Test Calorific Value calculation."""
    print("\n" + "="*60)
    print("TEST 1: Calorific Value (CV)")
    print("="*60)

    raw_data = {
        "batch": {
            "E": 9081.0,    # J/K
            "q1": 90.0,     # J
            "q2": 0.0       # J
        },
        "s_used": 0.5,      # Sulfur %
        "p1": {
            "m": 1.0,       # gram
            "delta_t": 2.5  # temperature rise
        },
        "p2": {
            "m": 1.0,
            "delta_t": 2.48
        }
    }

    result = calc_calorific_value_cv(raw_data)
    print(f"Raw data: {raw_data}")
    print(f"Result: {result:.2f} cal/g" if result else "Result: None")

    # Expected: ~5300-5400 cal/g for typical coal
    if result and 5000 <= result <= 6000:
        print("✅ PASS: CV within expected range")
    else:
        print("⚠️  WARNING: CV outside expected range (5000-6000 cal/g)")

    return result


def test_gi():
    """Test Gray-King Index calculation."""
    print("\n" + "="*60)
    print("TEST 2: Gray-King Index (Gi)")
    print("="*60)

    # Test 5:1 mode (default)
    raw_data_51 = {
        "p1": {
            "m1": 5.0,
            "m2": 0.5,
            "m3": 1.0
        },
        "p2": {
            "m1": 5.0,
            "m2": 0.5,
            "m3": 1.0
        }
    }

    result_51 = calc_gray_king_gi(raw_data_51)
    print(f"\n5:1 Mode (default):")
    print(f"Raw data: {raw_data_51}")
    print(f"Result: {result_51}" if result_51 else "Result: None")

    # Expected: 10 + (30*0.5 + 70*1.0)/5.0 = 10 + 85/5 = 10 + 17 = 27
    expected_51 = 27
    if result_51 == expected_51:
        print(f"✅ PASS: Gi = {result_51} (expected {expected_51})")
    else:
        print(f"❌ FAIL: Gi = {result_51} (expected {expected_51})")

    # Test 3:3 mode (retest)
    raw_data_33 = {
        "p1": {
            "m1": 5.0,
            "m2": 0.5,
            "m3": 1.0,
            "mode": "3:3"
        }
    }

    result_33 = calc_gray_king_gi(raw_data_33)
    print(f"\n3:3 Mode (retest):")
    print(f"Raw data: {raw_data_33}")
    print(f"Result: {result_33}" if result_33 else "Result: None")

    # Expected: (30*0.5 + 70*1.0)/(5*5.0) = 85/25 = 3.4 -> round(3.4) = 3
    expected_33 = 3
    if result_33 == expected_33:
        print(f"✅ PASS: Gi = {result_33} (expected {expected_33})")
    else:
        print(f"❌ FAIL: Gi = {result_33} (expected {expected_33})")

    return result_51, result_33


def test_fm():
    """Test Free Moisture calculation."""
    print("\n" + "="*60)
    print("TEST 3: Free Moisture (FM)")
    print("="*60)

    raw_data = {
        "p1": {
            "wt": 50.0,   # Tray weight
            "wb": 150.0,  # Before drying
            "wa": 120.0   # After drying
        },
        "p2": {
            "wt": 50.0,
            "wb": 150.0,
            "wa": 121.0
        }
    }

    result = calc_free_moisture_fm(raw_data)
    print(f"Raw data: {raw_data}")
    print(f"Result: {result:.2f}%" if result else "Result: None")

    # Expected for p1: ((150 - 120) / (120 - 50)) * 100 = (30 / 70) * 100 = 42.86%
    # Expected for p2: ((150 - 121) / (121 - 50)) * 100 = (29 / 71) * 100 = 40.85%
    # Average: ~41.85%
    if result and 40 <= result <= 45:
        print("✅ PASS: FM within expected range")
    else:
        print("⚠️  WARNING: FM outside expected range")

    return result


def test_solid():
    """Test Solid content calculation."""
    print("\n" + "="*60)
    print("TEST 4: Solid Content")
    print("="*60)

    raw_data = {
        "p1": {
            "a": 150.0,  # Total weight
            "b": 50.0,   # Container weight
            "c": 80.0    # Dry weight
        },
        "p2": {
            "a": 150.0,
            "b": 50.0,
            "c": 81.0
        }
    }

    result = calc_solid(raw_data)
    print(f"Raw data: {raw_data}")
    print(f"Result: {result:.2f}%" if result else "Result: None")

    # Expected for p1: (80 * 100) / (150 - 50) = 8000 / 100 = 80%
    # Expected for p2: (81 * 100) / (150 - 50) = 8100 / 100 = 81%
    # Average: 80.5%
    expected = 80.5
    if result and abs(result - expected) < 0.1:
        print(f"✅ PASS: Solid = {result:.2f}% (expected {expected}%)")
    else:
        print(f"❌ FAIL: Solid = {result:.2f}% (expected {expected}%)")

    return result


def test_trd():
    """Test True Relative Density calculation."""
    print("\n" + "="*60)
    print("TEST 5: True Relative Density (TRD)")
    print("="*60)

    raw_data = {
        "mad": 3.0,  # Moisture content from previous analysis
        "p1": {
            "m": 2.0,      # Coal sample mass
            "m1": 150.0,   # Bottle + water
            "m2": 151.5,   # Bottle + water + coal
            "temp": 20.0   # Temperature (°C)
        },
        "p2": {
            "m": 2.0,
            "m1": 150.0,
            "m2": 151.48,
            "temp": 20.0
        }
    }

    result = calc_trd(raw_data)
    print(f"Raw data: {raw_data}")
    print(f"Result: {result:.4f}" if result else "Result: None")

    # Expected calculation for p1:
    # md = 2.0 * (100 - 3.0) / 100 = 1.94
    # kt at 20°C = 0.99823
    # TRD = (1.94 / (1.94 + 151.5 - 150.0)) * 0.99823
    #     = (1.94 / 3.44) * 0.99823 = 0.5640 * 0.99823 ≈ 0.5630
    if result and 0.5 <= result <= 2.0:
        print("✅ PASS: TRD within expected range (0.5-2.0)")
    else:
        print("⚠️  WARNING: TRD outside expected range")

    return result


def test_verify_and_recalculate():
    """Test verify_and_recalculate with new calculations."""
    print("\n" + "="*60)
    print("TEST 6: verify_and_recalculate() Integration")
    print("="*60)

    # Test with Gi
    raw_data = {
        "p1": {"m1": 5.0, "m2": 0.5, "m3": 1.0},
        "p2": {"m1": 5.0, "m2": 0.5, "m3": 1.0}
    }

    client_result = 27.0
    server_result, warnings = verify_and_recalculate(
        analysis_code="Gi",
        client_final_result=client_result,
        raw_data=raw_data,
        user_id=1,
        sample_id=123
    )

    print(f"\nAnalysis: Gi")
    print(f"Client submitted: {client_result}")
    print(f"Server calculated: {server_result}")
    print(f"Warnings: {warnings if warnings else 'None'}")

    if server_result == client_result:
        print("✅ PASS: Client and server values match (no tampering)")
    else:
        print("⚠️  WARNING: Values don't match")

    # Test with tampered value
    print("\n--- Testing tampering detection ---")
    tampered_client = 99.99
    server_result2, warnings2 = verify_and_recalculate(
        analysis_code="Gi",
        client_final_result=tampered_client,
        raw_data=raw_data,
        user_id=1,
        sample_id=123
    )

    print(f"Tampered client value: {tampered_client}")
    print(f"Server calculated: {server_result2}")
    print(f"Warnings: {warnings2}")

    if warnings2:
        print("✅ PASS: Tampering detected and logged")
    else:
        print("❌ FAIL: Tampering not detected")

    return server_result, warnings


def main():
    """Run all tests."""
    print("\n" + "🔒"*30)
    print("SERVER-SIDE CALCULATION TESTS")
    print("Testing: CV, Gi, FM, Solid, TRD")
    print("🔒"*30)

    try:
        # Run all tests
        test_cv()
        test_gi()
        test_fm()
        test_solid()
        test_trd()
        test_verify_and_recalculate()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nОдоо эдгээр тооцоололууд /api/save_results endpoint-д")
        print("автоматаар ажиллаж, хакерласан утгыг илрүүлнэ!")
        print("\nБаримтжуулалт шинэчлэх хэрэгтэй:")
        print("- SERVER_SIDE_CALCULATION_SECURITY.md")
        print("- SERVER_CALCULATION_IMPLEMENTATION_COMPLETE.md")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
