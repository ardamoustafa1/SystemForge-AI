import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

export const options = {
  scenarios: {
    mixed_workload: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "2m", target: 50 },
        { duration: "30s", target: 0 }
      ],
      exec: "mixedFlow"
    }
  }
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/api";
const AUTH_COOKIE = __ENV.AUTH_COOKIE || "";
const CSRF = __ENV.CSRF || "";
const WORKSPACE_ID = __ENV.WORKSPACE_ID || "";

const errorRate = new Rate("errors");
const creationTrend = new Trend("design_creation_duration");

function authHeaders() {
  return {
    headers: {
      "content-type": "application/json",
      "x-csrf-token": CSRF,
      "x-workspace-id": WORKSPACE_ID,
      "cookie": AUTH_COOKIE
    }
  };
}

export function mixedFlow() {
  // 1. Health check (Smoke)
  let res = http.get(`${BASE_URL}/health`);
  check(res, { "health is 200": (r) => r.status === 200 });

  // 2. Create Design
  const payload = JSON.stringify({
    input: {
      project_title: `LoadTest-${__VU}-${__ITER}`,
      project_type: "Load test",
      problem_statement: "Mixed workload generation",
      expected_users: "10k",
      traffic_assumptions: "steady",
      preferred_stack: "FastAPI, Postgres, Redis",
      constraints: "Keep p95 low"
    },
    scale_stance: "balanced",
    output_language: "en"
  });

  const start = new Date().getTime();
  let createRes = http.post(`${BASE_URL}/designs`, payload, authHeaders());
  const success = check(createRes, { "create design 2xx": (r) => r.status >= 200 && r.status < 300 });
  errorRate.add(!success);
  creationTrend.add(new Date().getTime() - start);

  if (success) {
    const designId = JSON.parse(createRes.body).id;

    // 3. Poll for generation (simulating websocket wait)
    for (let i = 0; i < 5; i++) {
        sleep(2);
        let getRes = http.get(`${BASE_URL}/designs/${designId}`, authHeaders());
        check(getRes, { "get design 200": (r) => r.status === 200 });
    }

    // 4. Test Markdown Export Endpoint
    let exportRes = http.get(`${BASE_URL}/designs/${designId}/export?format=markdown`, authHeaders());
    check(exportRes, { "export markdown 200": (r) => r.status === 200 });
  }

  sleep(1);
}
