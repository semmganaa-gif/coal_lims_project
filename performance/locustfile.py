# -*- coding: utf-8 -*-
"""
Locust Load Test
Coal LIMS Performance Testing (Python alternative to k6)

Installation: pip install locust
Run: locust -f performance/locustfile.py --host=http://localhost:5000
"""
from locust import HttpUser, task, between, events
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LIMSUser(HttpUser):
    """Simulates a typical LIMS user."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    # Test credentials
    users = [
        {"username": "admin", "password": "admin123"},
        {"username": "chemist1", "password": "chemist123"},
    ]

    def on_start(self):
        """Login when user starts."""
        self.login()

    def login(self):
        """Perform login."""
        user = random.choice(self.users)

        # Get login page (for CSRF token if needed)
        response = self.client.get("/login")

        # Try to extract CSRF token
        csrf_token = ""
        if "csrf_token" in response.text:
            import re
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)

        # Perform login
        self.client.post("/login", data={
            "username": user["username"],
            "password": user["password"],
            "csrf_token": csrf_token,
        })

    @task(3)
    def view_dashboard(self):
        """View main dashboard - most common action."""
        self.client.get("/")

    @task(2)
    def view_samples(self):
        """View samples list."""
        self.client.get("/samples")

    @task(2)
    def view_workspace(self):
        """View analysis workspace."""
        self.client.get("/analysis/workspace")

    @task(1)
    def view_reports(self):
        """View reports page."""
        self.client.get("/reports")

    @task(1)
    def api_samples(self):
        """Call samples API."""
        self.client.get("/api/samples", headers={
            "Accept": "application/json"
        })


class AdminUser(HttpUser):
    """Simulates an admin user with additional tasks."""

    wait_time = between(2, 5)
    weight = 1  # Lower weight = fewer admin users

    def on_start(self):
        """Login as admin."""
        response = self.client.get("/login")

        csrf_token = ""
        if "csrf_token" in response.text:
            import re
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)

        self.client.post("/login", data={
            "username": "admin",
            "password": "admin123",
            "csrf_token": csrf_token,
        })

    @task(2)
    def view_admin(self):
        """View admin panel."""
        self.client.get("/admin/")

    @task(1)
    def view_users(self):
        """View users list."""
        self.client.get("/admin/users")

    @task(1)
    def view_settings(self):
        """View settings page."""
        self.client.get("/settings")


class HealthCheckUser(HttpUser):
    """Lightweight user for monitoring."""

    wait_time = between(5, 10)
    weight = 1

    @task
    def health_check(self):
        """Check health endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("Unhealthy status")
                except Exception:
                    response.failure("Invalid JSON")
            else:
                response.failure(f"Status {response.status_code}")


# Event handlers for custom reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests."""
    if response_time > 2000:  # Over 2 seconds
        logger.warning(f"Slow request: {request_type} {name} - {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary on test completion."""
    logger.info("=== Load Test Complete ===")
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
