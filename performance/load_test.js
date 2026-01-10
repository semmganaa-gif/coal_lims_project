/**
 * k6 Load Test Script
 * Coal LIMS Performance Testing
 *
 * Installation: https://k6.io/docs/getting-started/installation/
 * Run: k6 run performance/load_test.js
 */
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const samplesDuration = new Trend('samples_page_duration');
const apiDuration = new Trend('api_duration');

// Test configuration
export const options = {
  // Stages define the load pattern
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down
  ],

  // Thresholds for pass/fail
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% requests under 2s
    errors: ['rate<0.1'],                // Error rate under 10%
    login_duration: ['p(95)<3000'],      // Login under 3s
    samples_page_duration: ['p(95)<2000'], // Samples page under 2s
    api_duration: ['p(95)<1000'],        // API calls under 1s
  },
};

// Base URL - change for your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

// Test users
const users = [
  { username: 'admin', password: 'admin123' },
  { username: 'chemist1', password: 'chemist123' },
];

// Get random user
function getRandomUser() {
  return users[Math.floor(Math.random() * users.length)];
}

// Main test scenario
export default function () {
  const user = getRandomUser();
  let authCookie = '';

  group('Login Flow', function () {
    // Get login page
    const loginPage = http.get(`${BASE_URL}/login`);
    check(loginPage, {
      'login page status 200': (r) => r.status === 200,
    });

    // Extract CSRF token if present
    const csrfMatch = loginPage.body.match(/name="csrf_token".*?value="([^"]+)"/);
    const csrfToken = csrfMatch ? csrfMatch[1] : '';

    // Perform login
    const loginStart = Date.now();
    const loginRes = http.post(`${BASE_URL}/login`, {
      username: user.username,
      password: user.password,
      csrf_token: csrfToken,
    }, {
      redirects: 5,
    });
    loginDuration.add(Date.now() - loginStart);

    const loginSuccess = check(loginRes, {
      'login successful': (r) => r.status === 200 || r.status === 302,
      'redirected to dashboard': (r) => !r.url.includes('/login'),
    });

    errorRate.add(!loginSuccess);

    // Store cookies for subsequent requests
    if (loginRes.cookies && loginRes.cookies.session) {
      authCookie = `session=${loginRes.cookies.session[0].value}`;
    }
  });

  sleep(1);

  group('Dashboard', function () {
    const res = http.get(`${BASE_URL}/`, {
      headers: { Cookie: authCookie },
    });

    check(res, {
      'dashboard status 200': (r) => r.status === 200,
    });
  });

  sleep(0.5);

  group('Samples Page', function () {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/samples`, {
      headers: { Cookie: authCookie },
    });
    samplesDuration.add(Date.now() - start);

    const success = check(res, {
      'samples page status 200': (r) => r.status === 200,
      'samples page has content': (r) => r.body.length > 0,
    });

    errorRate.add(!success);
  });

  sleep(0.5);

  group('API Calls', function () {
    // Sample list API
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/samples`, {
      headers: {
        Cookie: authCookie,
        'Accept': 'application/json',
      },
    });
    apiDuration.add(Date.now() - start);

    check(res, {
      'API status 200': (r) => r.status === 200,
      'API returns JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('json'),
    });
  });

  sleep(0.5);

  group('Analysis Workspace', function () {
    const res = http.get(`${BASE_URL}/analysis/workspace`, {
      headers: { Cookie: authCookie },
    });

    check(res, {
      'workspace status 200': (r) => r.status === 200,
    });
  });

  sleep(0.5);

  group('Reports Page', function () {
    const res = http.get(`${BASE_URL}/reports`, {
      headers: { Cookie: authCookie },
    });

    check(res, {
      'reports status 200': (r) => r.status === 200 || r.status === 302,
    });
  });

  sleep(1);

  group('Logout', function () {
    const res = http.get(`${BASE_URL}/logout`, {
      headers: { Cookie: authCookie },
      redirects: 5,
    });

    check(res, {
      'logout successful': (r) => r.status === 200,
    });
  });

  sleep(1);
}

// Summary report handler
export function handleSummary(data) {
  return {
    'performance/results.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

// Text summary helper
function textSummary(data, options) {
  const { metrics } = data;
  let output = '\n=== COAL LIMS LOAD TEST RESULTS ===\n\n';

  output += `Total Requests: ${metrics.http_reqs.values.count}\n`;
  output += `Failed Requests: ${metrics.http_req_failed.values.passes}\n`;
  output += `Request Duration (avg): ${metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  output += `Request Duration (p95): ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  output += `Requests/sec: ${metrics.http_reqs.values.rate.toFixed(2)}\n\n`;

  if (metrics.login_duration) {
    output += `Login Duration (p95): ${metrics.login_duration.values['p(95)'].toFixed(2)}ms\n`;
  }
  if (metrics.samples_page_duration) {
    output += `Samples Page (p95): ${metrics.samples_page_duration.values['p(95)'].toFixed(2)}ms\n`;
  }
  if (metrics.api_duration) {
    output += `API Calls (p95): ${metrics.api_duration.values['p(95)'].toFixed(2)}ms\n`;
  }

  output += '\n=================================\n';
  return output;
}
