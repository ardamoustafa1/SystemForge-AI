"use client";

import { useEffect } from "react";
import { useI18n } from "@/i18n/i18n-context";
import { motion } from "framer-motion";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useI18n();

  useEffect(() => {
    // In production, we log this to Sentry/Telemetry
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center relative overflow-hidden bg-background">
      <div className="absolute inset-0 z-0 flex items-center justify-center opacity-20 pointer-events-none">
        <div className="absolute w-96 h-96 bg-red-500/20 rounded-full blur-3xl -translate-y-12"></div>
        <div className="absolute w-72 h-72 bg-orange-500/10 rounded-full blur-3xl translate-x-24 translate-y-24"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative z-10 text-center max-w-lg px-8 py-12 rounded-2xl glass-card border border-red-500/10 shadow-2xl backdrop-blur-xl"
      >
        <div className="w-16 h-16 mx-auto bg-red-500/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner border border-red-500/20">
          <AlertTriangle className="w-8 h-8 text-red-500/80" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight mb-3 text-white/90">
          {t("common.somethingWentWrong") || "System Anomaly Detected"}
        </h1>
        <p className="text-muted text-sm mb-8 leading-relaxed">
          Our core loop encountered an unexpected state. We have logged the
          trace for our engineers. Please attempt to reset the view.
        </p>

        <Button
          onClick={reset}
          className="bg-white/10 hover:bg-white/20 text-white border border-white/10 rounded-full px-6 transition-all"
        >
          <RefreshCcw className="w-4 h-4 mr-2" />
          {t("common.tryAgain") || "Reboot Sequence"}
        </Button>
      </motion.div>
    </div>
  );
}
