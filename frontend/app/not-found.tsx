"use client";

import Link from "next/link";
import { useI18n } from "@/i18n/i18n-context";
import { motion } from "framer-motion";
import { Compass, ArrowLeft } from "lucide-react";

export default function NotFoundPage() {
  const { t } = useI18n();

  return (
    <div className="min-h-[80vh] flex items-center justify-center relative overflow-hidden bg-background">
      {/* Abstract Background Effects */}
      <div className="absolute inset-0 z-0 flex items-center justify-center opacity-30 pointer-events-none">
        <div className="absolute w-96 h-96 bg-brand/20 rounded-full blur-3xl -translate-y-12"></div>
        <div className="absolute w-72 h-72 bg-blue-500/10 rounded-full blur-3xl translate-x-24 translate-y-24"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 text-center max-w-md px-6 py-12 rounded-2xl glass-card border border-border/50 shadow-2xl backdrop-blur-xl"
      >
        <motion.div
          initial={{ scale: 0.8, rotate: -15 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="w-20 h-20 mx-auto bg-brand/10 rounded-2xl flex items-center justify-center mb-8 shadow-inner"
        >
          <Compass className="w-10 h-10 text-brand opacity-80" />
        </motion.div>

        <h1 className="text-5xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/60">
          404
        </h1>
        <h2 className="text-2xl font-semibold mb-3">
          {t("common.pageNotFound")}
        </h2>
        <p className="text-muted text-base mb-8 leading-relaxed">
          The architecture coordinate you are trying to reach has drifted out of
          orbit. Let&apos;s get you back to the main workspace.
        </p>

        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-medium text-white bg-brand rounded-full hover:bg-brand/90 hover:scale-105 transition-all duration-200 shadow-lg shadow-brand/20"
        >
          <ArrowLeft className="w-4 h-4" />
          {t("common.backToHome")}
        </Link>
      </motion.div>
    </div>
  );
}
