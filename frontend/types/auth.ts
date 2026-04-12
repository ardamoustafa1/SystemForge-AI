export type AuthUser = {
  id: number;
  email: string;
  full_name: string;
};

export type LoginResponse = {
  user: AuthUser;
  csrf_token: string;
  expires_in_seconds: number;
};
