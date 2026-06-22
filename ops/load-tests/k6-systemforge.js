import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    designs: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "1m", target: 10 },
        { duration: "3m", target: 30 },
        { duration: "1m", target: 0 }
      ],
      exec: "designFlow"
    }
  }
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/api";
const AUTH_COOKIE = __ENV.AUTH_COOKIE || "";
const CSRF = __ENV.CSRF || "";
const WORKSPACE_ID = __ENV.WORKSPACE_ID || "";

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

export function designFlow() {
  const payload = JSON.stringify({
    input: {
      project_title: `k6-${__VU}-${__ITER}`,
      project_type: "Load test",
      problem_statement: "Load profile validation",
      expected_users: "10k",
      traffic_assumptions: "steady",
      preferred_stack: "FastAPI, Postgres, Redis",
      constraints: "Keep p95 low"
    },
    scale_stance: "balanced",
    output_language: "en"
  });
  const res = http.post(`${BASE_URL}/designs`, payload, authHeaders());
  check(res, { "create design 2xx": (r) => r.status >= 200 && r.status < 300 });
  sleep(1);
}

