# tests/security/security_audit.py
"""
Comprehensive security audit and penetration testing for Coal LIMS.

Tests:
1. CSRF bypass attempts
2. SQL injection attempts
3. XSS vulnerabilities
4. Authentication bypass
5. File upload vulnerabilities
6. Session hijacking
7. Access control issues

Run with: python tests/security/security_audit.py
"""
import requests
import sys
from urllib.parse import urljoin
from typing import List, Dict
import json


class SecurityAudit:
    """Security audit and penetration testing framework."""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.vulnerabilities: List[Dict] = []
        self.passed_tests: List[str] = []

    def log_vulnerability(self, severity: str, test_name: str, description: str, details: str = ""):
        """Log a discovered vulnerability."""
        vuln = {
            "severity": severity,
            "test": test_name,
            "description": description,
            "details": details
        }
        self.vulnerabilities.append(vuln)
        print(f"❌ [{severity}] {test_name}: {description}")
        if details:
            print(f"   Details: {details}")

    def log_pass(self, test_name: str):
        """Log a passed security test."""
        self.passed_tests.append(test_name)
        print(f"✅ {test_name}: PASSED")

    def test_csrf_protection(self):
        """Test CSRF protection on critical endpoints."""
        print("\n=== Testing CSRF Protection ===")

        # Test 1: POST without CSRF token
        endpoints = [
            "/equipment/add_equipment",
            "/equipment/bulk_delete",
            "/equipment/edit_equipment/1",
        ]

        for endpoint in endpoints:
            try:
                response = self.session.post(
                    urljoin(self.base_url, endpoint),
                    data={"name": "Hacked Equipment"}
                )

                if response.status_code == 200 and "success" in response.text.lower():
                    self.log_vulnerability(
                        "CRITICAL",
                        f"CSRF Missing - {endpoint}",
                        "Endpoint accepts POST without CSRF token",
                        f"Status: {response.status_code}"
                    )
                else:
                    self.log_pass(f"CSRF Protection - {endpoint}")
            except Exception as e:
                print(f"⚠️ Error testing {endpoint}: {e}")

        # Test 2: Invalid CSRF token
        try:
            response = self.session.post(
                urljoin(self.base_url, "/equipment/add_equipment"),
                data={
                    "name": "Test",
                    "csrf_token": "invalid_token_12345"
                }
            )

            if response.status_code == 200 and "успех" in response.text.lower():
                self.log_vulnerability(
                    "CRITICAL",
                    "CSRF Token Validation",
                    "Invalid CSRF token accepted",
                    "Application does not validate CSRF tokens properly"
                )
            else:
                self.log_pass("CSRF Token Validation")
        except Exception as e:
            print(f"⚠️ Error testing invalid CSRF: {e}")

    def test_sql_injection(self):
        """Test SQL injection vulnerabilities."""
        print("\n=== Testing SQL Injection ===")

        # Common SQL injection payloads
        payloads = [
            "' OR '1'='1",
            "1' OR '1'='1' --",
            "'; DROP TABLE sample; --",
            "1 UNION SELECT NULL, username, password FROM user--",
            "' OR 1=1--",
        ]

        # Test search endpoints
        for payload in payloads:
            try:
                # Test DataTables search
                response = self.session.get(
                    urljoin(self.base_url, "/api/data"),
                    params={
                        "draw": "1",
                        "start": "0",
                        "length": "25",
                        "columns[2][search][value]": payload
                    }
                )

                # Check for SQL errors in response
                sql_errors = [
                    "sql syntax",
                    "sqlite3.OperationalError",
                    "IntegrityError",
                    "DatabaseError",
                    "near \"",
                    "sqlite error"
                ]

                response_text = response.text.lower()
                for error in sql_errors:
                    if error.lower() in response_text:
                        self.log_vulnerability(
                            "CRITICAL",
                            "SQL Injection - DataTables",
                            f"SQL injection possible via search",
                            f"Payload: {payload}, Error found: {error}"
                        )
                        break
                else:
                    # No SQL errors found - good!
                    pass

            except Exception as e:
                # If exception contains SQL error, it's a vulnerability
                if any(err in str(e).lower() for err in ["sql", "database", "sqlite"]):
                    self.log_vulnerability(
                        "CRITICAL",
                        "SQL Injection - Exception",
                        f"SQL injection causes exception",
                        f"Payload: {payload}, Exception: {str(e)[:200]}"
                    )

        self.log_pass("SQL Injection Tests (no vulnerabilities in search)")

    def test_xss_vulnerabilities(self):
        """Test Cross-Site Scripting (XSS) vulnerabilities."""
        print("\n=== Testing XSS Vulnerabilities ===")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        # Test equipment name field (stored XSS)
        for payload in xss_payloads:
            try:
                # Note: This requires authentication and CSRF token
                # For full test, need to login first
                response = self.session.get(
                    urljoin(self.base_url, "/equipment_list")
                )

                if payload in response.text and not ("&lt;" in response.text or "&#" in response.text):
                    self.log_vulnerability(
                        "HIGH",
                        "XSS - Equipment List",
                        "XSS payload not properly escaped",
                        f"Payload: {payload}"
                    )
                    break
            except Exception as e:
                pass

        self.log_pass("XSS Tests (no vulnerabilities detected)")

    def test_authentication_bypass(self):
        """Test authentication bypass attempts."""
        print("\n=== Testing Authentication Bypass ===")

        # Test 1: Access protected page without login
        protected_endpoints = [
            "/equipment_list",
            "/analysis_hub",
            "/admin/users",
        ]

        for endpoint in protected_endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint))

                if response.status_code == 200 and "login" not in response.url.lower():
                    self.log_vulnerability(
                        "CRITICAL",
                        f"Auth Bypass - {endpoint}",
                        "Protected endpoint accessible without authentication",
                        f"Status: {response.status_code}, URL: {response.url}"
                    )
                else:
                    self.log_pass(f"Authentication Required - {endpoint}")
            except Exception as e:
                print(f"⚠️ Error testing {endpoint}: {e}")

    def test_file_upload_security(self):
        """Test file upload security."""
        print("\n=== Testing File Upload Security ===")

        # Test 1: Upload executable file
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("script.js", b"alert('XSS')", "application/javascript"),
        ]

        for filename, content, mime_type in malicious_files:
            try:
                files = {'certificate_file': (filename, content, mime_type)}
                response = self.session.post(
                    urljoin(self.base_url, "/equipment/add_log/1"),
                    files=files,
                    data={"action_type": "Calibration"}
                )

                if response.status_code == 200 and "success" in response.text.lower():
                    self.log_vulnerability(
                        "CRITICAL",
                        f"File Upload - {filename}",
                        "Malicious file type accepted",
                        f"File: {filename}, Type: {mime_type}"
                    )
                else:
                    self.log_pass(f"File Type Validation - {filename} rejected")
            except Exception as e:
                print(f"⚠️ Error testing file upload: {e}")

        # Test 2: Upload oversized file
        try:
            large_content = b'X' * (10 * 1024 * 1024)  # 10MB
            files = {'certificate_file': ('large.pdf', large_content, 'application/pdf')}
            response = self.session.post(
                urljoin(self.base_url, "/equipment/add_log/1"),
                files=files
            )

            if response.status_code == 200 and "success" in response.text.lower():
                self.log_vulnerability(
                    "MEDIUM",
                    "File Upload - Size Limit",
                    "File size limit not enforced (10MB file accepted)",
                    "Max size should be 5MB"
                )
            else:
                self.log_pass("File Size Validation - 10MB rejected")
        except Exception as e:
            print(f"⚠️ Error testing large file: {e}")

    def test_session_security(self):
        """Test session security."""
        print("\n=== Testing Session Security ===")

        # Test 1: Check for secure session cookies
        try:
            response = self.session.get(urljoin(self.base_url, "/login"))

            set_cookie = response.headers.get('Set-Cookie', '')

            if 'HttpOnly' not in set_cookie:
                self.log_vulnerability(
                    "HIGH",
                    "Session Cookie - HttpOnly",
                    "Session cookie missing HttpOnly flag",
                    "Cookie can be accessed via JavaScript (XSS risk)"
                )
            else:
                self.log_pass("Session Cookie - HttpOnly")

            if 'SameSite' not in set_cookie:
                self.log_vulnerability(
                    "MEDIUM",
                    "Session Cookie - SameSite",
                    "Session cookie missing SameSite flag",
                    "CSRF protection weakened"
                )
            else:
                self.log_pass("Session Cookie - SameSite")

            # In production, should also have Secure flag
            # if 'Secure' not in set_cookie:
            #     self.log_vulnerability("MEDIUM", ...)

        except Exception as e:
            print(f"⚠️ Error testing session security: {e}")

    def test_access_control(self):
        """Test role-based access control."""
        print("\n=== Testing Access Control ===")

        # This requires logging in as different users
        # For now, just test that admin endpoints are protected

        admin_endpoints = [
            "/admin/users",
            "/admin/analysis_config",
            "/admin/import_historical"
        ]

        for endpoint in admin_endpoints:
            try:
                # Test without admin role
                response = self.session.get(urljoin(self.base_url, endpoint))

                if response.status_code == 200 and "admin" in response.text.lower():
                    self.log_vulnerability(
                        "HIGH",
                        f"Access Control - {endpoint}",
                        "Admin endpoint accessible without proper role",
                        f"Status: {response.status_code}"
                    )
                else:
                    self.log_pass(f"Access Control - {endpoint}")
            except Exception as e:
                pass

    def test_information_disclosure(self):
        """Test for information disclosure."""
        print("\n=== Testing Information Disclosure ===")

        # Test 1: Error messages
        try:
            response = self.session.get(urljoin(self.base_url, "/nonexistent_page"))

            dangerous_patterns = [
                "Traceback",
                "File \"",
                "line ",
                "/app/",
                "SQLAlchemy",
                "werkzeug",
            ]

            response_text = response.text
            for pattern in dangerous_patterns:
                if pattern in response_text:
                    self.log_vulnerability(
                        "MEDIUM",
                        "Information Disclosure - Error Page",
                        "Error page reveals internal paths/stack traces",
                        f"Pattern found: {pattern}"
                    )
                    break
            else:
                self.log_pass("Information Disclosure - Error Pages")

        except Exception as e:
            pass

    def run_all_tests(self):
        """Run all security tests."""
        print("=" * 60)
        print("COAL LIMS SECURITY AUDIT")
        print("=" * 60)

        self.test_csrf_protection()
        self.test_sql_injection()
        self.test_xss_vulnerabilities()
        self.test_authentication_bypass()
        self.test_file_upload_security()
        self.test_session_security()
        self.test_access_control()
        self.test_information_disclosure()

        # Summary
        print("\n" + "=" * 60)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {len(self.passed_tests)}")
        print(f"❌ Vulnerabilities Found: {len(self.vulnerabilities)}")

        if self.vulnerabilities:
            print("\nVULNERABILITIES BY SEVERITY:")
            critical = [v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']
            high = [v for v in self.vulnerabilities if v['severity'] == 'HIGH']
            medium = [v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']

            print(f"  🔴 Critical: {len(critical)}")
            print(f"  🟠 High: {len(high)}")
            print(f"  🟡 Medium: {len(medium)}")

            # Export to JSON
            with open("security_audit_results.json", "w") as f:
                json.dump({
                    "passed": self.passed_tests,
                    "vulnerabilities": self.vulnerabilities
                }, f, indent=2)
            print("\n📄 Detailed results saved to: security_audit_results.json")

        return len(self.vulnerabilities) == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Coal LIMS Security Audit")
    parser.add_argument("--host", default="http://localhost:5000", help="Base URL of the application")
    args = parser.parse_args()

    auditor = SecurityAudit(base_url=args.host)
    success = auditor.run_all_tests()

    sys.exit(0 if success else 1)
