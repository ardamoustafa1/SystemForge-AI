const ENV = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api",
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "SystemForge AI",
};

export function getEnv() {
  return ENV;
}

export function getWebSocketUrl() {
  const normalizedApiUrl = ENV.apiUrl.replace(/\/$/, "");
  let wsBase = normalizedApiUrl;
  if (normalizedApiUrl.startsWith("https://")) {
    wsBase = normalizedApiUrl.replace(/^https:\/\//, "wss://");
  } else if (normalizedApiUrl.startsWith("http://")) {
    wsBase = normalizedApiUrl.replace(/^http:\/\//, "ws://");
  }

  // Backend websocket gateway lives at `${api_prefix}/ws`.
  if (wsBase.endsWith("/ws")) {
    return wsBase;
  }
  return `${wsBase}/ws`;
}
