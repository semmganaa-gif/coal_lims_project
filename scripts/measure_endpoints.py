"""Endpoint response time measurement.

Зорилго: Чухал хуудаснуудыг олон удаа дуудаж дундаж хариу хугацааг хэмжих.
Bottleneck-уудыг олох.

Хэрэглээ:
    # 1. Login session-тай тест:
    python scripts/measure_endpoints.py --base http://127.0.0.1:5000 --user admin --password Test12345!

    # 2. Тус endpoint-ыг 10 удаа дуудаж дундаж + p50/p95-ыг тооцоолно

Output: per-endpoint statistic + table summary.
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print('pip install requests required')
    sys.exit(1)


ENDPOINTS = [
    ('GET',  '/api/v1/sample_summary',            'Negtgel page (HTML shell)'),
    ('GET',  '/api/v1/sample_summary/page?offset=0&limit=100', 'Negtgel page-1 (100 row)'),
    ('GET',  '/api/v1/sample_summary/page?offset=0&limit=100&start_date=2026-04-17&end_date=2026-05-17', 'Negtgel page filtered'),
    ('GET',  '/api/v1/archive_hub',               'Archive hub (tree only)'),
    ('GET',  '/api/v1/archive_hub?client=CHPP&type=2h&year=2026&month=5', 'Archive hub (drill render)'),
    ('GET',  '/api/v1/archive_hub/page?client=CHPP&type=2h&year=2026&month=5&offset=0&limit=100', 'Archive page-1 (100 row)'),
    ('GET',  '/api/v1/archive_hub/page?client=CHPP&type=2h&offset=0&limit=100', 'Archive page (no year filter)'),
    ('GET',  '/ahlah_dashboard',                  'Ahlah hyanalt'),
    ('GET',  '/api/ahlah_data',                   'Ahlah data API'),
    ('GET',  '/api/ahlah_stats',                  'Ahlah stats'),
    ('GET',  '/equipment_journal/grid?category=all', 'Equipment journal'),
    ('GET',  '/api/equipment/usage_summary?start_date=2026-04-01&end_date=2026-05-17&category=all', 'Equipment usage summary'),
    ('GET',  '/api/equipment/journal_detailed?start_date=2026-04-01&end_date=2026-05-17&category=all', 'Equipment journal detailed'),
    ('GET',  '/api/v1/morning_dashboard?lab=coal','Morning dashboard'),
    ('GET',  '/index',                            'Sample list'),
    ('GET',  '/equipment',                        'Equipment list'),
]


def login(base_url, username, password):
    session = requests.Session()
    # Get login page for CSRF token
    r = session.get(f'{base_url}/login')
    if r.status_code != 200:
        raise RuntimeError(f'Login page status {r.status_code}')
    # Extract CSRF token
    import re
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError('CSRF token not found')
    csrf = m.group(1)
    # Submit login
    r = session.post(f'{base_url}/login', data={
        'csrf_token': csrf,
        'username': username,
        'password': password,
        'remember_me': '',
    }, allow_redirects=False)
    if r.status_code not in (302, 303):
        raise RuntimeError(f'Login failed: status {r.status_code}')
    return session


def measure(session, base_url, method, path, runs=5):
    """endpoint-ыг N удаа дуудаж response time-уудыг буцаах."""
    url = f'{base_url}{path}'
    times = []
    sizes = []
    last_status = None
    for _ in range(runs):
        t0 = time.perf_counter()
        if method == 'GET':
            r = session.get(url, allow_redirects=False, timeout=60)
        else:
            r = session.post(url, allow_redirects=False, timeout=60)
        elapsed = time.perf_counter() - t0
        times.append(elapsed * 1000)  # to ms
        sizes.append(len(r.content))
        last_status = r.status_code
    return times, sizes, last_status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:5000')
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', default='Test12345!')
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--warmup', type=int, default=1, help='cold runs to discard')
    args = parser.parse_args()

    print(f'Target: {args.base} | User: {args.user} | Runs/endpoint: {args.runs} (warmup: {args.warmup})')
    print()

    print('Logging in...')
    session = login(args.base, args.user, args.password)
    print('  [OK]Logged in')
    print()

    results = []
    for method, path, name in ENDPOINTS:
        print(f'Testing {method} {path}')
        try:
            times, sizes, status = measure(session, args.base, method, path,
                                            runs=args.runs + args.warmup)
            # Discard warmup runs
            measured = times[args.warmup:]
            sizes_m = sizes[args.warmup:]
            avg = statistics.mean(measured)
            p50 = statistics.median(measured)
            p95 = max(measured) if len(measured) <= 2 else sorted(measured)[int(len(measured) * 0.95)]
            mn = min(measured)
            mx = max(measured)
            avg_size = statistics.mean(sizes_m) / 1024
            results.append((name, path, status, avg, p50, p95, mn, mx, avg_size))
            print(f'  status={status} avg={avg:.0f}ms p50={p50:.0f}ms p95={p95:.0f}ms size={avg_size:.0f}KB')
        except Exception as e:
            print(f'  ERROR: {e}')
            results.append((name, path, 'ERR', None, None, None, None, None, None))

    print()
    print('=' * 110)
    print(f'{"Endpoint":<35} {"Status":<7} {"avg":>7} {"p50":>7} {"p95":>7} {"min":>7} {"max":>7} {"size":>7}')
    print('-' * 110)
    for name, path, status, avg, p50, p95, mn, mx, sz in results:
        if avg is None:
            print(f'{name:<35} {status:<7} ERROR')
            continue
        flag = ''
        if avg > 3000:
            flag = ' [SLOW]'
        elif avg > 1000:
            flag = ' [warn]'
        print(f'{name:<35} {status:<7} {avg:>6.0f}ms {p50:>6.0f}ms {p95:>6.0f}ms {mn:>6.0f}ms {mx:>6.0f}ms {sz:>6.0f}KB{flag}')
    print('=' * 110)


if __name__ == '__main__':
    main()
