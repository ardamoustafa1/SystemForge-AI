const ENV = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api",
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "SystemForge AI",
};

export function getEnv() {
  return ENV;
}
