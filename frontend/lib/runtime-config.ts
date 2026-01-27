type RuntimeConfig = {
  NEXT_PUBLIC_API_BASE_URL?: string;
};

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const runtimeConfig = (window as Window & { __RUNTIME_CONFIG__?: RuntimeConfig })
      .__RUNTIME_CONFIG__;
    if (runtimeConfig?.NEXT_PUBLIC_API_BASE_URL) {
      return runtimeConfig.NEXT_PUBLIC_API_BASE_URL;
    }
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
}
