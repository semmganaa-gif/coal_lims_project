# tests/load/locustfile.py
"""
Load testing script for Coal LIMS using Locust.

Tests performance improvements from:
- Pagination (equipment list, samples list)
- Database indexes on foreign keys
- Bulk query optimizations

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:5000

Then open http://localhost:8089 for web UI
"""
import random
from locust import HttpUser, task, between, SequentialTaskSet
import json


class EquipmentListLoadTest(SequentialTaskSet):
    """Test equipment list pagination under load."""

    @task
    def login(self):
        """Login as test user."""
        self.client.post("/login", data={
            "username": "admin",
            "password": "admin"  # Change to your test credentials
        })

    @task(10)
    def view_equipment_list_page_1(self):
        """Load first page of equipment list."""
        self.client.get("/equipment_list?page=1")

    @task(5)
    def view_equipment_list_page_2(self):
        """Load second page of equipment list."""
        self.client.get("/equipment_list?page=2")

    @task(3)
    def view_equipment_list_page_random(self):
        """Load random page to test pagination."""
        page = random.randint(1, 10)
        self.client.get(f"/equipment_list?page={page}")

    @task(2)
    def view_equipment_detail(self):
        """View equipment detail (tests foreign key indexes)."""
        # Assuming equipment IDs 1-100 exist
        eq_id = random.randint(1, 100)
        self.client.get(f"/equipment/equipment_detail/{eq_id}")


class SampleListLoadTest(SequentialTaskSet):
    """Test sample list pagination and index performance."""

    @task
    def login(self):
        """Login as test user."""
        self.client.post("/login", data={
            "username": "admin",
            "password": "admin"
        })

    @task(10)
    def view_samples_datatable(self):
        """Test DataTables pagination (uses indexes)."""
        params = {
            "draw": "1",
            "start": "0",
            "length": "25",
            "search[value]": ""
        }
        self.client.get("/api/data", params=params)

    @task(5)
    def view_samples_page_2(self):
        """Test DataTables second page."""
        params = {
            "draw": "2",
            "start": "25",
            "length": "25",
            "search[value]": ""
        }
        self.client.get("/api/data", params=params)

    @task(3)
    def search_samples_by_code(self):
        """Test search with indexed sample_code."""
        # This tests the index on sample.sample_code
        params = {
            "draw": "1",
            "start": "0",
            "length": "25",
            "columns[2][search][value]": "TEST"  # Search in sample_code column
        }
        self.client.get("/api/data", params=params)

    @task(2)
    def filter_by_date_range(self):
        """Test date range filter (uses received_date index)."""
        params = {
            "draw": "1",
            "start": "0",
            "length": "25",
            "dateFilterStart": "2024-01-01",
            "dateFilterEnd": "2024-12-31"
        }
        self.client.get("/api/data", params=params)


class DatabaseIndexPerformanceTest(SequentialTaskSet):
    """Test performance of database operations using foreign key indexes."""

    @task
    def login(self):
        """Login as test user."""
        self.client.post("/login", data={
            "username": "admin",
            "password": "admin"
        })

    @task(10)
    def mass_save_operation(self):
        """Test bulk update performance (benefits from sample_id index)."""
        # This tests the N+1 query fix and index on AnalysisResult.sample_id
        payload = {
            "items": [
                {"sample_id": i, "weight": 100 + i}
                for i in range(1, 21)  # 20 samples
            ],
            "mark_ready": True
        }
        response = self.client.post(
            "/api/mass/save",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    @task(5)
    def sample_summary_with_joins(self):
        """Test sample summary page (uses multiple foreign key indexes)."""
        # This benefits from indexes on:
        # - AnalysisResult.sample_id
        # - AnalysisResult.status
        # - Sample.user_id
        self.client.get("/api/sample_summary?page=1")

    @task(3)
    def analysis_results_by_sample(self):
        """Test fetching analysis results (uses sample_id index)."""
        sample_id = random.randint(1, 100)
        # Simulate query that benefits from AnalysisResult.sample_id index
        self.client.get(f"/api/sample_history/{sample_id}")


class ConcurrentWriteTest(SequentialTaskSet):
    """Test concurrent write operations for race conditions."""

    @task
    def login(self):
        """Login as test user."""
        self.client.post("/login", data={
            "username": "admin",
            "password": "admin"
        })

    @task(5)
    def concurrent_mass_updates(self):
        """Test concurrent mass updates (race condition test)."""
        sample_ids = [random.randint(1, 100) for _ in range(10)]
        payload = {
            "items": [{"sample_id": sid, "weight": random.randint(50, 200)} for sid in sample_ids],
            "mark_ready": True
        }
        self.client.post(
            "/api/mass/save",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    @task(3)
    def concurrent_sample_creation(self):
        """Test concurrent sample creation (transaction atomicity test)."""
        code = f"LOAD{random.randint(1000, 9999)}"
        data = {
            "client_name": "LoadTest",
            "sample_type": "Coal",
            "sample_condition": "dry",
            "submitted_codes": code,
            "list_type": "single_uniform"
        }
        self.client.post("/index", data=data)


class CoalLIMSUser(HttpUser):
    """
    Simulated user for load testing Coal LIMS.

    This user randomly performs different task sets to simulate
    realistic usage patterns.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    tasks = {
        EquipmentListLoadTest: 3,  # 30% of users
        SampleListLoadTest: 4,      # 40% of users
        DatabaseIndexPerformanceTest: 2,  # 20% of users
        ConcurrentWriteTest: 1      # 10% of users
    }


class PaginationBenchmark(HttpUser):
    """
    Specialized benchmark for pagination performance.

    Tests the improvement from adding pagination to equipment list.
    Before: loads all 10,000+ records
    After: loads only 50 records per page
    """
    wait_time = between(0.5, 1)  # Faster requests for benchmarking

    @task
    def benchmark_paginated_list(self):
        """Benchmark paginated equipment list."""
        page = random.randint(1, 20)
        self.client.get(f"/equipment_list?page={page}&per_page=50")


class IndexBenchmark(HttpUser):
    """
    Specialized benchmark for database index performance.

    Tests queries that benefit from the new foreign key indexes:
    - AnalysisResult.sample_id
    - AnalysisResult.user_id
    - Sample.user_id
    - etc.
    """
    wait_time = between(0.5, 1)

    @task(5)
    def benchmark_analysis_results_by_sample(self):
        """Benchmark query using AnalysisResult.sample_id index."""
        sample_id = random.randint(1, 1000)
        # This query benefits from index on sample_id
        self.client.get(f"/api/sample_history/{sample_id}")

    @task(3)
    def benchmark_sample_with_user_join(self):
        """Benchmark query using Sample.user_id index."""
        # DataTables query that joins samples with users
        params = {
            "draw": "1",
            "start": "0",
            "length": "25"
        }
        self.client.get("/api/data", params=params)

    @task(2)
    def benchmark_bulk_result_query(self):
        """Benchmark bulk query for multiple samples (uses indexes)."""
        # This benefits from bulk loading optimization
        sample_ids = [random.randint(1, 1000) for _ in range(20)]
        self.client.get(f"/api/sample_summary?page=1")


# =============================================================================
# BENCHMARK SCENARIOS
# =============================================================================

class BeforePaginationScenario(HttpUser):
    """
    Simulates load BEFORE pagination was added.
    Use this to compare baseline performance.
    """
    wait_time = between(1, 2)

    @task
    def load_all_equipment_no_pagination(self):
        """Load all equipment without pagination (OLD behavior)."""
        # If you kept the old endpoint for comparison
        self.client.get("/equipment_list_old_no_pagination")


class AfterPaginationScenario(HttpUser):
    """
    Simulates load AFTER pagination was added.
    Compare with BeforePaginationScenario to measure improvement.
    """
    wait_time = between(1, 2)

    @task
    def load_paginated_equipment(self):
        """Load paginated equipment list (NEW behavior)."""
        page = random.randint(1, 10)
        self.client.get(f"/equipment_list?page={page}")


# =============================================================================
# RUN INSTRUCTIONS
# =============================================================================
"""
# Basic load test (web UI):
locust -f tests/load/locustfile.py --host=http://localhost:5000

# Headless mode with specific users and spawn rate:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
       --users 100 --spawn-rate 10 --run-time 1m --headless

# Test only pagination:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
       --users 50 --spawn-rate 5 PaginationBenchmark --headless

# Test only indexes:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
       --users 50 --spawn-rate 5 IndexBenchmark --headless

# Export results:
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
       --users 100 --spawn-rate 10 --run-time 5m \
       --html=load_test_report.html --headless
"""
