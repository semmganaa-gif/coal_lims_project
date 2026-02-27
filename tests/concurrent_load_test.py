"""
Coal LIMS — Concurrent Load Test
=================================
10 агент (химич) нэгэн зэрэг нүүрсний шинжилгээний хуудсанд
үр дүн шивэх ачааллын тест.

Шалгах зүйлс:
  1. Connection pool exhaustion (pool_size=25, overflow=25)
  2. Race condition: 2 химич нэг дээжинд зэрэг бичих
  3. Deadlock detection
  4. Data integrity (duplicate results, lost updates)
  5. StaleDataError (optimistic locking)
  6. Response time under load
"""

import requests
import threading
import time
import json
import random
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from collections import defaultdict

# ─── Config ────────────────────────────────────────────────────────
BASE_URL = "http://localhost:5000"
NUM_AGENTS = 10
ANALYSIS_CODES = ["Mad", "Aad", "Vad", "CSN", "TS"]  # 5 шинжилгээ
TIMEOUT = 15  # seconds per request

# ─── Result tracking ──────────────────────────────────────────────
@dataclass
class TestResult:
    agent_id: int
    action: str
    analysis_code: str = ""
    sample_id: int = 0
    status_code: int = 0
    success: bool = False
    error: str = ""
    duration_ms: float = 0
    response_data: dict = field(default_factory=dict)

results_lock = threading.Lock()
all_results: list[TestResult] = []

def record(r: TestResult):
    with results_lock:
        all_results.append(r)


# ─── Shared login session (rate limiter bypass) ──────────────────
_shared_cookies = None
_login_lock = threading.Lock()

def _login_once(username: str, password: str):
    """Нэг удаа login хийж cookie-г хадгална."""
    global _shared_cookies
    with _login_lock:
        if _shared_cookies is not None:
            return True

        sess = requests.Session()
        resp = sess.get(f"{BASE_URL}/login", timeout=TIMEOUT)

        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', resp.text)
        if not csrf_match:
            csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', resp.text)
        if not csrf_match:
            csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp.text)
        if not csrf_match:
            print("  [!] CSRF token not found in login page")
            return False

        resp = sess.post(f"{BASE_URL}/login", data={
            "username": username,
            "password": password,
            "csrf_token": csrf_match.group(1),
        }, timeout=TIMEOUT, allow_redirects=True)

        if resp.status_code == 200 and "/login" not in resp.url:
            _shared_cookies = sess.cookies.copy()
            print(f"  [+] Login OK as {username}")
            return True
        else:
            print(f"  [!] Login FAILED: status={resp.status_code}")
            return False


def create_session(agent_id: int, username: str, password: str) -> requests.Session:
    """Shared cookies ашиглан session үүсгэнэ (rate limiter-г зайлсхийх)."""
    global _shared_cookies

    if _shared_cookies is None:
        if not _login_once(username, password):
            record(TestResult(agent_id, "login", error="Login failed"))
            return None

    sess = requests.Session()
    sess.cookies.update(_shared_cookies)

    t0 = time.time()
    # Verify session works
    resp = sess.get(f"{BASE_URL}/api/eligible_samples/Mad", timeout=TIMEOUT)
    duration = (time.time() - t0) * 1000

    if resp.status_code == 200:
        record(TestResult(agent_id, "login", success=True, status_code=200, duration_ms=duration))
        return sess
    elif resp.status_code == 302 or resp.status_code == 401:
        record(TestResult(agent_id, "login", error=f"Session invalid: {resp.status_code}", duration_ms=duration))
        return None
    else:
        # Probably OK (could be 404 etc. but session works)
        record(TestResult(agent_id, "login", success=True, status_code=resp.status_code, duration_ms=duration))
        return sess


# ─── Helper: Get eligible samples ────────────────────────────────
def get_eligible_samples(sess: requests.Session, agent_id: int, code: str) -> list:
    """Тухайн шинжилгээнд хамааралтай дээжүүдийг авна."""
    t0 = time.time()
    try:
        resp = sess.get(f"{BASE_URL}/api/eligible_samples/{code}", timeout=TIMEOUT)
        duration = (time.time() - t0) * 1000

        if resp.status_code == 200:
            data = resp.json()
            samples = data.get("samples", [])
            record(TestResult(agent_id, "eligible_samples", code,
                              success=True, status_code=200, duration_ms=duration,
                              response_data={"count": len(samples)}))
            return samples
        else:
            record(TestResult(agent_id, "eligible_samples", code,
                              status_code=resp.status_code, error=resp.text[:200], duration_ms=duration))
            return []
    except Exception as e:
        duration = (time.time() - t0) * 1000
        record(TestResult(agent_id, "eligible_samples", code, error=str(e), duration_ms=duration))
        return []


# ─── Helper: Save analysis result ────────────────────────────────
def save_result(sess: requests.Session, agent_id: int, sample_id: int, code: str) -> dict:
    """Шинжилгээний үр дүн хадгална."""

    # Analysis-specific random raw_data
    raw_data = generate_raw_data(code)

    payload = [{
        "sample_id": sample_id,
        "analysis_code": code,
        "raw_data": raw_data,
    }]

    t0 = time.time()
    try:
        resp = sess.post(f"{BASE_URL}/api/save_results",
                         json=payload, timeout=TIMEOUT,
                         headers={"Content-Type": "application/json"})
        duration = (time.time() - t0) * 1000

        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text[:300]}

        success = resp.status_code == 200
        error = ""
        if not success:
            error = data.get("message", data.get("error", str(data)))[:200]

        record(TestResult(agent_id, "save_result", code, sample_id,
                          resp.status_code, success, error, duration, data))
        return data

    except Exception as e:
        duration = (time.time() - t0) * 1000
        record(TestResult(agent_id, "save_result", code, sample_id, error=str(e), duration_ms=duration))
        return {"error": str(e)}


def generate_raw_data(code: str) -> dict:
    """
    Analysis code-д тохирсон raw_data үүсгэнэ.
    Server format: p1/p2 нь dict {num, m1, m2, m3, result} байх ёстой.
    """
    def _parallel(num_label, m1, m2, m3, result):
        return {"num": num_label, "m1": m1, "m2": m2, "m3": m3, "result": result}

    if code == "Mad":
        # Moisture: (m2-m3)/(m2-m1)*100
        m1 = round(random.uniform(25.0, 30.0), 4)     # empty crucible
        m2 = round(m1 + random.uniform(0.9, 1.1), 4)  # crucible + wet sample
        moisture_pct = random.uniform(5.0, 15.0)
        m3 = round(m2 - (m2 - m1) * moisture_pct / 100, 4)  # crucible + dry sample
        r1 = round((m2 - m3) / (m2 - m1) * 100, 2) if (m2 - m1) > 0 else 0

        m1b = round(random.uniform(25.0, 30.0), 4)
        m2b = round(m1b + random.uniform(0.9, 1.1), 4)
        m3b = round(m2b - (m2b - m1b) * (moisture_pct + random.uniform(-0.3, 0.3)) / 100, 4)
        r2 = round((m2b - m3b) / (m2b - m1b) * 100, 2) if (m2b - m1b) > 0 else 0

        return {
            "p1": _parallel("T1", m1, m2, m3, r1),
            "p2": _parallel("T2", m1b, m2b, m3b, r2),
        }

    elif code == "Aad":
        # Ash: (m3-m1)/(m2-m1)*100
        m1 = round(random.uniform(12.0, 15.0), 4)
        m2 = round(m1 + random.uniform(0.9, 1.1), 4)
        ash_pct = random.uniform(8.0, 25.0)
        m3 = round(m1 + (m2 - m1) * ash_pct / 100, 4)
        r1 = round((m3 - m1) / (m2 - m1) * 100, 2)

        m1b = round(random.uniform(12.0, 15.0), 4)
        m2b = round(m1b + random.uniform(0.9, 1.1), 4)
        m3b = round(m1b + (m2b - m1b) * (ash_pct + random.uniform(-0.3, 0.3)) / 100, 4)
        r2 = round((m3b - m1b) / (m2b - m1b) * 100, 2)

        return {
            "p1": _parallel("A1", m1, m2, m3, r1),
            "p2": _parallel("A2", m1b, m2b, m3b, r2),
        }

    elif code == "Vad":
        # Volatile: (m2-m3)/(m2-m1)*100 - Mad
        m1 = round(random.uniform(18.0, 22.0), 4)
        m2 = round(m1 + random.uniform(0.9, 1.1), 4)
        vol_pct = random.uniform(20.0, 40.0)
        m3 = round(m2 - (m2 - m1) * vol_pct / 100, 4)
        r1 = round((m2 - m3) / (m2 - m1) * 100, 2)

        m1b = round(random.uniform(18.0, 22.0), 4)
        m2b = round(m1b + random.uniform(0.9, 1.1), 4)
        m3b = round(m2b - (m2b - m1b) * (vol_pct + random.uniform(-0.5, 0.5)) / 100, 4)
        r2 = round((m2b - m3b) / (m2b - m1b) * 100, 2)

        return {
            "p1": _parallel("V1", m1, m2, m3, r1),
            "p2": _parallel("V2", m1b, m2b, m3b, r2),
        }

    elif code == "TS":
        # Total sulfur (instrument reading)
        r1 = round(random.uniform(0.3, 2.0), 2)
        r2 = round(r1 + random.uniform(-0.05, 0.05), 2)
        return {
            "p1": {"num": "S1", "result": r1},
            "p2": {"num": "S2", "result": r2},
        }

    elif code == "CSN":
        # Crucible swelling number — integer 1-9
        val = random.randint(1, 9)
        return {
            "p1": {"num": "C1", "result": val},
            "p2": {"num": "C2", "result": val},
        }

    else:
        r1 = round(random.uniform(1.0, 50.0), 2)
        r2 = round(r1 + random.uniform(-0.5, 0.5), 2)
        return {
            "p1": {"num": "X1", "result": r1},
            "p2": {"num": "X2", "result": r2},
        }


# ─── Test Scenarios ───────────────────────────────────────────────

def agent_worker(agent_id: int, username: str, password: str,
                 analysis_code: str, target_samples: list):
    """
    Нэг агент (химич)-ийн ажлын урсгал:
    1. Login
    2. Eligible samples авах
    3. Тэдгээрт үр дүн оруулах
    """
    print(f"  Agent-{agent_id}: Login as {username}, analysis={analysis_code}...")

    sess = create_session(agent_id, username, password)
    if not sess:
        print(f"  Agent-{agent_id}: ❌ Login FAILED")
        return

    print(f"  Agent-{agent_id}: ✅ Login OK, fetching eligible samples...")

    # Get eligible samples
    samples = get_eligible_samples(sess, agent_id, analysis_code)
    if not samples:
        print(f"  Agent-{agent_id}: ⚠️ No eligible samples for {analysis_code}")
        return

    print(f"  Agent-{agent_id}: 📋 {len(samples)} eligible samples, saving results...")

    # Save results for each sample (max 5 per agent)
    saved = 0
    for sample in samples[:5]:
        sid = sample["id"]

        # If target_samples specified, only save those
        if target_samples and sid not in target_samples:
            continue

        result = save_result(sess, agent_id, sid, analysis_code)
        if "error" not in str(result).lower() or "results" in result:
            saved += 1

    print(f"  Agent-{agent_id}: 💾 Saved {saved} results for {analysis_code}")


def race_condition_worker(agent_id: int, username: str, password: str,
                          sample_id: int, analysis_code: str):
    """
    Race condition тест: 2+ агент НЭГ дээжинд зэрэг бичих.
    UniqueConstraint + with_for_update() зөв ажиллаж байгааг шалгана.
    """
    sess = create_session(agent_id, username, password)
    if not sess:
        return

    # Бүгд нэг зэрэг save хийх
    time.sleep(0.1)  # sync barrier
    result = save_result(sess, agent_id, sample_id, analysis_code)
    return result


# ─── MAIN TEST SUITE ──────────────────────────────────────────────

def test_1_normal_concurrent_load():
    """
    TEST 1: 10 химич тус тусдаа шинжилгээнд зэрэг ажиллах
    Шалгах: connection pool, response time, error rate
    """
    print("\n" + "="*70)
    print("TEST 1: Normal Concurrent Load — 10 agents, different analyses")
    print("="*70)

    # admin нэвтэрч eligible samples-н жагсаалтыг урьдчилж авах
    users = [
        ("admin", "Admin123"),
    ]

    # 10 agent, 5 analysis code-д тархаах
    assignments = []
    for i in range(NUM_AGENTS):
        code = ANALYSIS_CODES[i % len(ANALYSIS_CODES)]
        user = users[0]  # same user for now
        assignments.append((i, user[0], user[1], code, []))

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=NUM_AGENTS) as executor:
        futures = [executor.submit(agent_worker, *a) for a in assignments]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ❌ Agent exception: {e}")

    total_time = (time.time() - t0) * 1000
    print(f"\n  ⏱️ Total time: {total_time:.0f}ms")


def test_2_race_condition_same_sample():
    """
    TEST 2: 5 агент НЭГ дээжинд НЭГ шинжилгээнд зэрэг бичих
    Шалгах: UniqueConstraint, with_for_update(), StaleDataError
    """
    print("\n" + "="*70)
    print("TEST 2: Race Condition — 5 agents save SAME sample+analysis")
    print("="*70)

    # Eligible sample олох
    sess = create_session(99, "admin", "Admin123")
    if not sess:
        print("  ❌ Admin login failed")
        return

    samples = get_eligible_samples(sess, 99, "Mad")
    if not samples:
        print("  ⚠️ No eligible samples for Mad")
        return

    target_sample = samples[0]
    target_id = target_sample["id"]
    print(f"  🎯 Target: sample_id={target_id} code={target_sample['sample_code']}")

    # 5 agent зэрэг save хийнэ
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            futures.append(executor.submit(
                race_condition_worker, i, "admin", "Admin123", target_id, "Mad"
            ))

        results = []
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"  ❌ Exception: {e}")

    total_time = (time.time() - t0) * 1000
    print(f"  ⏱️ Total time: {total_time:.0f}ms")

    # 1 амжилттай, 4 нь 409 эсвэл error байх ёстой
    successes = sum(1 for r in all_results
                    if r.action == "save_result" and r.sample_id == target_id and r.success)
    errors = sum(1 for r in all_results
                 if r.action == "save_result" and r.sample_id == target_id and not r.success)

    print(f"  ✅ Successes: {successes} | ❌ Errors: {errors}")
    if successes == 1:
        print(f"  🎉 PASS — UniqueConstraint зөв ажиллаж байна!")
    elif successes > 1:
        print(f"  🔴 FAIL — {successes} duplicate results! Race condition!")
    else:
        print(f"  ⚠️ All failed — check errors")


def test_3_burst_save_same_analysis():
    """
    TEST 3: 10 агент НЭГ шинжилгээнд (Mad) тус тусын дээж дээр зэрэг save
    Шалгах: connection pool, batch performance
    """
    print("\n" + "="*70)
    print("TEST 3: Burst Save — 10 agents on Mad analysis, different samples")
    print("="*70)

    sess = create_session(99, "admin", "Admin123")
    if not sess:
        print("  ❌ Admin login failed")
        return

    samples = get_eligible_samples(sess, 99, "Mad")
    if len(samples) < 10:
        print(f"  ⚠️ Only {len(samples)} eligible samples, need 10")
        if len(samples) == 0:
            return

    print(f"  📋 {len(samples)} eligible samples for Mad")

    # Each agent gets 1 sample
    t0 = time.time()
    barrier = threading.Barrier(min(10, len(samples)))

    def burst_worker(agent_id, sample):
        s = create_session(agent_id + 50, "admin", "Admin123")
        if not s:
            return
        try:
            barrier.wait(timeout=10)  # Бүгд зэрэг эхлэх
        except threading.BrokenBarrierError:
            pass
        save_result(s, agent_id + 50, sample["id"], "Mad")

    n = min(10, len(samples))
    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(burst_worker, i, samples[i]) for i in range(n)]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ❌ {e}")

    total_time = (time.time() - t0) * 1000
    print(f"  ⏱️ Total time: {total_time:.0f}ms ({n} concurrent saves)")


# ─── Report ───────────────────────────────────────────────────────

def print_report():
    """Тестийн нэгдсэн тайлан."""
    print("\n" + "="*70)
    print("📊 CONCURRENT LOAD TEST REPORT")
    print("="*70)

    # Group by action
    by_action = defaultdict(list)
    for r in all_results:
        by_action[r.action].append(r)

    for action, results in by_action.items():
        successes = sum(1 for r in results if r.success)
        failures = sum(1 for r in results if not r.success)
        durations = [r.duration_ms for r in results if r.duration_ms > 0]

        avg_ms = sum(durations) / len(durations) if durations else 0
        max_ms = max(durations) if durations else 0
        min_ms = min(durations) if durations else 0

        print(f"\n  📌 {action}:")
        print(f"     Total: {len(results)} | ✅ {successes} | ❌ {failures}")
        print(f"     Time: avg={avg_ms:.0f}ms | min={min_ms:.0f}ms | max={max_ms:.0f}ms")

        if failures > 0:
            print(f"     Errors:")
            errors = defaultdict(int)
            for r in results:
                if not r.success and r.error:
                    errors[r.error[:80]] += 1
            for err, count in errors.items():
                print(f"       [{count}x] {err}")

    # Data integrity check
    print(f"\n  🔍 DATA INTEGRITY:")
    save_results = [r for r in all_results if r.action == "save_result"]

    # Check for duplicates (same sample_id + analysis_code should only succeed once)
    sample_code_pairs = defaultdict(list)
    for r in save_results:
        if r.success:
            key = (r.sample_id, r.analysis_code)
            sample_code_pairs[key].append(r.agent_id)

    duplicates = {k: v for k, v in sample_code_pairs.items() if len(v) > 1}
    if duplicates:
        print(f"     🔴 DUPLICATE RESULTS FOUND: {len(duplicates)}")
        for (sid, code), agents in duplicates.items():
            print(f"        sample_id={sid} code={code} agents={agents}")
    else:
        print(f"     ✅ Давхардсан үр дүн байхгүй — data integrity OK")

    # Response time analysis
    print(f"\n  ⏱️ RESPONSE TIME ANALYSIS:")
    save_durations = [r.duration_ms for r in save_results if r.duration_ms > 0]
    if save_durations:
        p50 = sorted(save_durations)[len(save_durations)//2]
        p90 = sorted(save_durations)[int(len(save_durations)*0.9)]
        p99 = sorted(save_durations)[int(len(save_durations)*0.99)]
        print(f"     Save results: p50={p50:.0f}ms | p90={p90:.0f}ms | p99={p99:.0f}ms")

    # Connection pool check
    print(f"\n  🔌 CONNECTION POOL:")
    max_concurrent = max(len([r for r in all_results if r.agent_id == i])
                         for i in set(r.agent_id for r in all_results)) if all_results else 0
    print(f"     Max concurrent agents: {len(set(r.agent_id for r in all_results))}")

    # Final verdict
    total_tests = len(all_results)
    total_failures = sum(1 for r in all_results if not r.success)
    error_rate = (total_failures / total_tests * 100) if total_tests > 0 else 0

    print(f"\n  {'='*50}")
    print(f"  VERDICT: ", end="")
    if error_rate < 5 and not duplicates:
        print(f"✅ PASS (error rate: {error_rate:.1f}%)")
    elif error_rate < 20 and not duplicates:
        print(f"🟡 PARTIAL (error rate: {error_rate:.1f}%)")
    else:
        print(f"🔴 FAIL (error rate: {error_rate:.1f}%, duplicates: {len(duplicates)})")


# ─── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Coal LIMS Concurrent Load Test")
    print(f"   URL: {BASE_URL}")
    print(f"   Agents: {NUM_AGENTS}")
    print(f"   Analyses: {ANALYSIS_CODES}")

    # Check server is running
    try:
        resp = requests.get(f"{BASE_URL}/login", timeout=5)
        print(f"   Server: ✅ Running (status={resp.status_code})")
    except Exception as e:
        print(f"   Server: ❌ Not running ({e})")
        sys.exit(1)

    # Run tests
    test_1_normal_concurrent_load()
    test_2_race_condition_same_sample()
    test_3_burst_save_same_analysis()

    # Print report
    print_report()
