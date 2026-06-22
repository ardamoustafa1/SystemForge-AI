"use client";
import { useEffect } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";

export function ThemeSync() {
  const { data: settings } = useSWR<{ theme: string }>(
    "/users/me/settings",
    api,
  );

  useEffect(() => {
    if (settings?.theme) {
      if (settings.theme === "light") {
        document.documentElement.classList.add("light");
        document.documentElement.classList.remove("dark");
      } else {
        document.documentElement.classList.add("dark");
        document.documentElement.classList.remove("light");
      }
    }
  }, [settings?.theme]);

  return null;
}
