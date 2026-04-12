import { apiClient } from "@/lib/api-client";
import { AuthUser, LoginResponse } from "@/types/auth";

type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
};

type LoginPayload = {
  email: string;
  password: string;
};

export async function register(payload: RegisterPayload) {
  return apiClient<AuthUser>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload: LoginPayload) {
  return apiClient<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function me() {
  return apiClient<AuthUser>("/auth/me");
}

export async function logout() {
  return apiClient<{ ok: boolean }>("/auth/logout", { method: "POST" });
}
