/**
 * k6 Smoke Test
 * Quick validation that system is working
 *
 * Run: k6 run performance/smoke_test.js
 */
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,           // 1 virtual user
  duration: '30s',  // Run for 30 seconds

  thresholds: {
    http_req_duration: ['p(99)<1500'],  // 99% under 1.5s
    http_req_failed: ['rate<0.01'],     // Less than 1% failures
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export default function () {
  // Health check
  const health = http.get(`${BASE_URL}/health`);
  check(health, {
    'health check OK': (r) => r.status === 200,
    'health response valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'healthy';
      } catch {
        return false;
      }
    },
  });

  // Login page loads
  const login = http.get(`${BASE_URL}/login`);
  check(login, {
    'login page loads': (r) => r.status === 200,
    'login page has form': (r) => r.body.includes('password'),
  });
}
