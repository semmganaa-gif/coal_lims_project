# run_tests.py
# -*- coding: utf-8 -*-
"""
Comprehensive test runner for Coal LIMS.

Executes all test suites and generates reports:
1. Unit tests (error handling)
2. Integration tests (CSRF protection)
3. Security audit
4. Instructions for load testing

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Only unit tests
    python run_tests.py --integration      # Only integration tests
    python run_tests.py --security         # Only security audit
    python run_tests.py --coverage         # Run with coverage report
"""
import sys
import subprocess
import os
from datetime import datetime
import json

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class TestRunner:
    """Orchestrates all test suites for Coal LIMS."""

    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "timestamp": self.timestamp,
            "unit_tests": None,
            "integration_tests": None,
            "security_audit": None,
        }

    def print_header(self, title):
        """Print formatted section header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def run_unit_tests(self, with_coverage=False):
        """Run unit tests for error handling."""
        self.print_header("UNIT TESTS - Error Handling")

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/test_error_handling.py",
            "-v",
            "--tb=short",
        ]

        if with_coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
            ])

        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["unit_tests"] = {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
            }

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            self.results["unit_tests"] = {"error": str(e), "passed": False}
            return False

    def run_integration_tests(self):
        """Run integration tests for CSRF protection."""
        self.print_header("INTEGRATION TESTS - CSRF Protection")

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_csrf_protection.py",
            "-v",
            "--tb=short",
        ]

        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["integration_tests"] = {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
            }

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            self.results["integration_tests"] = {"error": str(e), "passed": False}
            return False

    def run_security_audit(self):
        """Run security audit and penetration tests."""
        self.print_header("SECURITY AUDIT - Penetration Testing")

        print("⚠️  NOTE: Security audit requires the Flask app to be running.")
        print("    Start the app with: python run.py")
        print("    Then run: python tests/security/security_audit.py")
        print()

        # Check if app is running by trying to import it
        try:
            # We can run the security audit in standalone mode
            cmd = [
                sys.executable,
                "tests/security/security_audit.py",
                "--host", "http://localhost:5000"
            ]

            print("Attempting to run security audit...")
            print("(This will fail if the app is not running on port 5000)")
            print()

            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=60)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["security_audit"] = {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
            }

            # Check if results file was created
            results_file = os.path.join(self.project_root, "security_audit_results.json")
            if os.path.exists(results_file):
                print(f"\n📄 Security audit results saved to: {results_file}")
                with open(results_file, 'r') as f:
                    audit_data = json.load(f)
                    vuln_count = len(audit_data.get('vulnerabilities', []))
                    if vuln_count > 0:
                        print(f"⚠️  Found {vuln_count} vulnerabilities - review the report!")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⏱️  Security audit timed out (app may not be running)")
            self.results["security_audit"] = {"error": "timeout", "passed": False}
            return False
        except Exception as e:
            print(f"ℹ️  Security audit skipped: {e}")
            print("    To run security audit:")
            print("    1. Start the app: python run.py")
            print("    2. Run: python tests/security/security_audit.py")
            self.results["security_audit"] = {"skipped": True, "reason": str(e)}
            return True  # Don't fail the whole suite if security audit can't run

    def show_load_testing_instructions(self):
        """Show instructions for running load tests."""
        self.print_header("LOAD TESTING - Pagination & Database Indexes")

        print("""
Load testing requires the application to be running and uses Locust.

QUICK START:
------------
1. Start the Flask app:
   python run.py

2. Run Locust with web UI (recommended):
   locust -f tests/load/locustfile.py --host=http://localhost:5000

3. Open browser to: http://localhost:8089
   - Set number of users: 50
   - Spawn rate: 5 users/sec
   - Run time: 2 minutes

HEADLESS MODE (for CI/CD):
--------------------------
# Test all scenarios:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \\
       --users 100 --spawn-rate 10 --run-time 2m --headless \\
       --html=load_test_report.html

# Test only pagination performance:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \\
       --users 50 --spawn-rate 5 PaginationBenchmark --headless

# Test only database index performance:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \\
       --users 50 --spawn-rate 5 IndexBenchmark --headless

AVAILABLE TEST SCENARIOS:
-------------------------
- CoalLIMSUser: Mixed usage patterns (default)
- PaginationBenchmark: Test pagination improvements
- IndexBenchmark: Test database index performance
- EquipmentListLoadTest: Equipment list specific tests
- SampleListLoadTest: Sample list and DataTables tests
- DatabaseIndexPerformanceTest: Foreign key index tests
- ConcurrentWriteTest: Race condition tests

WHAT TO LOOK FOR:
-----------------
- Response time: Should be < 500ms for paginated lists
- Failure rate: Should be 0%
- RPS (requests per second): Higher is better
- Compare with/without pagination to see improvements
        """)

    def generate_summary_report(self):
        """Generate summary report of all test results."""
        self.print_header("TEST SUMMARY REPORT")

        # Count results
        passed_count = 0
        failed_count = 0
        skipped_count = 0

        for test_name, result in self.results.items():
            if test_name == "timestamp":
                continue

            if result is None:
                skipped_count += 1
            elif isinstance(result, dict):
                if result.get("passed"):
                    passed_count += 1
                elif result.get("skipped"):
                    skipped_count += 1
                else:
                    failed_count += 1

        print(f"Timestamp: {self.results['timestamp']}\n")
        print(f"✅ Passed:  {passed_count}")
        print(f"❌ Failed:  {failed_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        print()

        # Detailed results
        print("DETAILED RESULTS:")
        print("-" * 70)

        for test_name, result in self.results.items():
            if test_name == "timestamp":
                continue

            status_icon = "⏭️"
            if result and isinstance(result, dict):
                if result.get("passed"):
                    status_icon = "✅"
                elif result.get("skipped"):
                    status_icon = "⏭️"
                else:
                    status_icon = "❌"

            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result}")

        print()

        # Save results to JSON
        results_file = f"test_results_{self.timestamp}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📄 Full results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results to JSON: {e}")

        print()

        # Overall status
        if failed_count == 0:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {failed_count} TEST SUITE(S) FAILED")
            return False

    def run_all(self, with_coverage=False):
        """Run all test suites."""
        print("\n" + "=" * 70)
        print("  COAL LIMS - COMPREHENSIVE TEST SUITE")
        print("  Testing High-Priority Fixes")
        print("=" * 70)

        # Run tests
        self.run_unit_tests(with_coverage=with_coverage)
        self.run_integration_tests()
        self.run_security_audit()
        self.show_load_testing_instructions()

        # Generate summary
        all_passed = self.generate_summary_report()

        return all_passed


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Coal LIMS Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--security", action="store_true", help="Run only security audit")
    parser.add_argument("--load", action="store_true", help="Show load testing instructions")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    args = parser.parse_args()

    runner = TestRunner()

    # If specific test requested, run only that
    if args.unit:
        success = runner.run_unit_tests(with_coverage=args.coverage)
        sys.exit(0 if success else 1)

    if args.integration:
        success = runner.run_integration_tests()
        sys.exit(0 if success else 1)

    if args.security:
        success = runner.run_security_audit()
        sys.exit(0 if success else 1)

    if args.load:
        runner.show_load_testing_instructions()
        sys.exit(0)

    # Otherwise run all tests
    success = runner.run_all(with_coverage=args.coverage)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
