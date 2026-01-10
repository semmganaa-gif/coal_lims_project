/**
 * k6 Stress Test
 * Find system limits under extreme load
 *
 * Run: k6 run performance/stress_test.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp to 50 users
    { duration: '2m', target: 50 },   // Stay at 50
    { duration: '1m', target: 100 },  // Ramp to 100 users
    { duration: '2m', target: 100 },  // Stay at 100
    { duration: '1m', target: 200 },  // Ramp to 200 users (stress)
    { duration: '2m', target: 200 },  // Stay at 200 (max stress)
    { duration: '2m', target: 0 },    // Ramp down
  ],

  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95% under 5s (relaxed for stress)
    errors: ['rate<0.3'],               // Up to 30% errors acceptable
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export default function () {
  // Simple GET requests to main endpoints
  const endpoints = [
    '/health',
    '/login',
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE_URL}${endpoint}`);

  const success = check(res, {
    'status is 2xx or 3xx': (r) => r.status >= 200 && r.status < 400,
    'response time OK': (r) => r.timings.duration < 5000,
  });

  errorRate.add(!success);
  sleep(0.1);
}
