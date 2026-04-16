import { getEnv } from "@/lib/env";
import { getActiveWorkspaceId } from "@/lib/workspace-context";

type ApiErrorPayload = {
  detail?: string;
  message?: string;
  error?: {
    message?: string;
    code?: string;
  };
};

function getCookie(name: string) {
  if (typeof document === "undefined") return null;
  const value = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
  return value ?? null;
}

export async function apiClient<T>(path: string, init?: RequestInit): Promise<T> {
  const { apiUrl } = getEnv();
  const headers = new Headers(init?.headers ?? {});
  headers.set("Content-Type", "application/json");
  const method = (init?.method ?? "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCookie("sf_csrf_token");
    if (csrf) headers.set("x-csrf-token", decodeURIComponent(csrf));
  }
  const workspaceId = getActiveWorkspaceId();
  if (workspaceId) headers.set("X-Workspace-Id", String(workspaceId));

  const doRequest = () =>
    fetch(`${apiUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      credentials: "include",
    });
  let response = await doRequest();
  if (response.status === 401 && !path.startsWith("/auth/")) {
    const refreshed = await fetch(`${apiUrl}/auth/refresh`, { method: "POST", credentials: "include" });
    if (refreshed.ok) {
      response = await doRequest();
    }
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new Error(payload.error?.message ?? payload.detail ?? payload.message ?? "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

/** Binary responses (e.g. PDF export). Does not force JSON Content-Type on the request. */
export async function apiBlob(path: string, init?: RequestInit): Promise<Blob> {
  const { apiUrl } = getEnv();
  const headers = new Headers(init?.headers ?? {});
  const method = (init?.method ?? "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCookie("sf_csrf_token");
    if (csrf) headers.set("x-csrf-token", decodeURIComponent(csrf));
  }

  const doRequest = () =>
    fetch(`${apiUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      credentials: "include",
    });
  let response = await doRequest();
  if (response.status === 401 && !path.startsWith("/auth/")) {
    const refreshed = await fetch(`${apiUrl}/auth/refresh`, { method: "POST", credentials: "include" });
    if (refreshed.ok) {
      response = await doRequest();
    }
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new Error(payload.error?.message ?? payload.detail ?? payload.message ?? "Request failed");
  }

  return response.blob();
}

/** Unauthenticated JSON fetch (e.g. public share links). */
export async function apiPublic<T>(path: string): Promise<T> {
  const { apiUrl } = getEnv();
  const response = await fetch(`${apiUrl}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new Error(payload.error?.message ?? payload.detail ?? payload.message ?? "Request failed");
  }

  return (await response.json()) as T;
}

/** Unauthenticated binary download (e.g. public PDF). */
export async function apiBlobPublic(path: string): Promise<Blob> {
  const { apiUrl } = getEnv();
  const response = await fetch(`${apiUrl}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new Error(payload.error?.message ?? payload.detail ?? payload.message ?? "Request failed");
  }

  return response.blob();
}
