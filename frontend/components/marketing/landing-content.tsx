"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Layers, Shield, Zap, GitCommit, FileSearch, Database, Globe2, Server, Rocket, Bot, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n/i18n-context";

const features = [
  { titleKey: "landing.feature1Title", descKey: "landing.feature1Desc" },
  { titleKey: "landing.feature2Title", descKey: "landing.feature2Desc" },
  { titleKey: "landing.feature3Title", descKey: "landing.feature3Desc" },
  { titleKey: "landing.feature4Title", descKey: "landing.feature4Desc" },
  { titleKey: "landing.feature5Title", descKey: "landing.feature5Desc" },
  { titleKey: "landing.feature6Title", descKey: "landing.feature6Desc" },
];

const useCases = [
  "landing.useCase1",
  "landing.useCase2",
  "landing.useCase3",
  "landing.useCase4",
  "landing.useCase5",
  "landing.useCase6",
];

const riseIn = {
  initial: { opacity: 0, y: 14 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: { duration: 0.45, ease: "easeOut" as const },
};

export function LandingContent() {
  const { t } = useI18n();
  return (
    <main className="relative overflow-hidden bg-background">
      {/* Subtle Premium Color Spotlight Effect */}
      <div className="pointer-events-none absolute left-0 right-0 top-0 -z-10 h-[800px] w-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-500/[0.07] via-background to-background" />
      <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 top-0 -z-10 h-[500px] w-[800px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-500/[0.06] via-transparent to-transparent opacity-60 mix-blend-screen" />
      
      <section className="container-page py-20 sm:py-32 relative z-10">
        <motion.div className="mx-auto max-w-4xl text-center" {...riseIn}>
          <div className="inline-flex items-center justify-center rounded-full border border-white/5 bg-white/[0.02] px-4 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur-md transition-colors hover:bg-white/[0.05]">
            <span className="mr-2 flex h-2 w-2 rounded-full bg-white/40"></span>
            {t("landing.badge")}
          </div>
          <h1 className="mt-8 text-4xl font-medium tracking-tight sm:text-7xl lg:text-[5rem] leading-[1.1]">
            {t("landing.heroTitle1")}
            <span className="mt-2 block bg-gradient-to-b from-white via-indigo-100 to-indigo-200/50 bg-clip-text text-transparent">
              {t("landing.heroTitle2")}
            </span>
          </h1>
          <p className="mx-auto mt-8 max-w-2xl text-base text-muted-foreground sm:text-xl font-light">
            {t("landing.heroDesc")}
          </p>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
            <Link href="/auth/sign-up">
              <Button className="h-12 rounded-full px-8 bg-white text-black hover:bg-white/90 shadow-[0_0_20px_rgba(255,255,255,0.1)] transition-all hover:scale-105 active:scale-95 text-sm font-medium">
                {t("landing.ctaPrimary")}
              </Button>
            </Link>
            <Link href="/auth/sign-in">
              <Button variant="outline" className="h-12 rounded-full border-white/10 bg-transparent text-white px-8 transition-all hover:bg-white/5 hover:border-white/20 active:scale-95 text-sm font-medium">
                {t("landing.ctaSecondary")}
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Minimal Mock Window */}
        <motion.div className="mx-auto mt-24 max-w-5xl" {...riseIn} transition={{ delay: 0.2, duration: 0.8 }}>
          <div className="relative rounded-2xl border border-white/10 bg-[#0a0a0a] shadow-[0_20px_80px_-20px_rgba(0,0,0,1)] ring-1 ring-white/5 transform-gpu transition-all">
            {/* Minimal Window Header */}
            <div className="flex items-center border-b border-white/5 bg-white/[0.02] px-4 py-3">
              <div className="flex gap-2 opacity-80 hover:opacity-100 transition-opacity duration-300">
                <div className="h-3 w-3 rounded-full bg-[#ff5f56] shadow-[0_0_8px_#ff5f5640]"></div>
                <div className="h-3 w-3 rounded-full bg-[#ffbd2e] shadow-[0_0_8px_#ffbd2e40]"></div>
                <div className="h-3 w-3 rounded-full bg-[#27c93f] shadow-[0_0_8px_#27c93f40]"></div>
              </div>
              <div className="mx-auto text-[11px] font-medium tracking-wider text-muted-foreground font-mono uppercase">
                {t("landing.sample")}
              </div>
              <div className="w-[52px]"></div> {/* spacer for centering */}
            </div>
            
            {/* Window Content */}
            <div className="grid gap-8 p-8 md:grid-cols-2 lg:gap-12 text-left">
              <div>
                <h3 className="flex items-center gap-2 text-sm font-medium tracking-wide text-white/90">
                  <span className="text-white/30">/</span> {t("landing.archSummary")}
                </h3>
                <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground font-mono">
                  {t("landing.sampleSummaryText")}
                </p>
                <div className="mt-8 h-px w-full bg-border/50"></div>
                <h3 className="mt-8 flex items-center gap-2 text-sm font-medium tracking-wide text-white/90">
                  <span className="text-white/30">/</span> {t("landing.topTradeoff")}
                </h3>
                <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground font-mono">
                  {t("landing.topTradeoffText")}
                </p>
              </div>
              
              {/* Monochromatic Scorecard */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 transition-colors hover:bg-white/[0.03]">
                <div className="relative">
                  <p className="mb-6 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    {t("landing.scorecard")}
                  </p>
                  <div className="space-y-5 font-mono text-[13px]">
                    {[
                      { label: "Scalability", score: 8 },
                      { label: "Reliability", score: 7 },
                      { label: "Security", score: 8 },
                      { label: "Maintainability", score: 8 },
                      { label: "Cost Efficiency", score: 8 },
                      { label: "Simplicity", score: 7 }
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between group">
                        <span className="text-white/60 group-hover:text-white/90 transition-colors">{item.label}</span>
                        <div className="flex items-center gap-4">
                          <div className="h-1 w-24 overflow-hidden bg-white/10 rounded-full">
                            <motion.div 
                              initial={{ width: 0 }}
                              whileInView={{ width: `${item.score * 10}%` }}
                              transition={{ delay: 0.5 + idx * 0.1, duration: 1, ease: "easeOut" }}
                              className="h-full bg-gradient-to-r from-indigo-500/80 to-blue-400/80 rounded-full"
                            />
                          </div>
                          <span className="w-8 text-right text-muted-foreground">{item.score}/10</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section id="features" className="container-page py-32 relative z-10 border-t border-white/[0.02] overflow-hidden">
        <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[600px] w-[1000px] -translate-x-1/2 -translate-y-1/3 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-500/[0.08] via-transparent to-transparent opacity-60 mix-blend-screen" />
        <motion.div className="text-center" {...riseIn}>
          <h2 className="text-4xl font-medium tracking-tight sm:text-5xl text-white block bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent pb-1">{t("landing.featuresTitle")}</h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/40 font-light">
            {t("landing.featuresSubtitle")}
          </p>
        </motion.div>
        <div className="mt-20 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div key={feature.titleKey} {...riseIn} transition={{ ...riseIn.transition, delay: index * 0.05 }}>
              <div className="group relative h-full rounded-3xl border border-white/5 bg-[#0a0a0a] p-8 overflow-hidden transition-all duration-300 hover:border-white/10 hover:bg-[#0c0c0e] hover:shadow-[0_20px_40px_-20px_rgba(0,0,0,0.5)]">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                
                <div className="relative z-10">
                  <div className="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] ring-1 ring-white/5 transition-all duration-500 group-hover:scale-110 group-hover:bg-indigo-500/10 group-hover:ring-indigo-500/20 group-hover:shadow-[0_0_20px_rgba(99,102,241,0.1)]">
                    {(() => {
                      const Icon = [Layers, GitCommit, Shield, Zap, FileSearch, Database][index % 6];
                      return <Icon className="h-6 w-6 text-white/40 group-hover:text-indigo-400 transition-colors duration-300" strokeWidth={1.5} />;
                    })()}
                  </div>
                  <h3 className="text-xl font-medium tracking-wide text-white/90">{t(feature.titleKey)}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-white/40 font-light">{t(feature.descKey)}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="use-cases" className="container-page py-32 relative z-10 border-t border-white/[0.02]">
        <motion.div className="text-center" {...riseIn}>
           <h2 className="text-4xl font-medium tracking-tight sm:text-5xl text-white block bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent pb-1">{t("landing.useCasesTitle")}</h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/40 font-light">{t("landing.useCasesSubtitle")}</p>
        </motion.div>
        <div className="mt-20 grid gap-5 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
          {useCases.map((item, index) => (
            <motion.div key={item} {...riseIn} transition={{ ...riseIn.transition, delay: index * 0.03 }}>
              <div className="group relative flex items-center gap-5 rounded-2xl border border-white/5 bg-[#09090b] p-5 shadow-[inset_0_1px_rgba(255,255,255,0.02),0_4px_10px_-5px_rgba(0,0,0,0.5)] transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/30 hover:bg-[#0c0c0e] hover:shadow-[0_15px_30px_-10px_rgba(99,102,241,0.15)] cursor-default">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500/0 via-indigo-500/0 to-indigo-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/[0.02] ring-1 ring-white/5 transition-all duration-300 group-hover:bg-indigo-500/10 group-hover:ring-indigo-500/30 group-hover:shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                  {(() => {
                      const Icon = [Globe2, Server, Shield, Rocket, Bot, Target][index % 6];
                      return <Icon className="h-5 w-5 text-white/40 group-hover:text-indigo-400 transition-colors duration-300" strokeWidth={1.5} />;
                  })()}
                </div>
                <p className="text-sm font-medium tracking-wide text-white/60 group-hover:text-white/95 transition-colors duration-300 leading-snug">{t(item)}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="comparison" className="container-page py-24 relative z-10 mb-20 border-t border-white/[0.02]">
        <motion.div {...riseIn}>
           <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#0a0a0a]">
            <div className="border-b border-white/5 px-8 py-10 md:px-12 md:py-14 text-center">
              <h2 className="text-3xl font-medium tracking-tight sm:text-4xl text-white/90">{t("landing.whyNotTitle")}</h2>
              <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground font-light">
                {t("landing.comparisonSubtitle")}
              </p>
            </div>
            
            <div className="grid md:grid-cols-2">
              <div className="border-b border-white/5 p-8 md:p-12 md:border-b-0 md:border-r">
                <div className="mb-6 inline-flex items-center rounded bg-white/5 px-2.5 py-1 text-xs font-medium text-white/40 uppercase tracking-widest">
                  Typical Process
                </div>
                <h3 className="text-lg font-medium text-white/70">{t("landing.genericWorkflow")}</h3>
                <ul className="mt-6 space-y-5 text-sm text-muted-foreground">
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-rose-500/50 font-bold">✕</span> {t("landing.generic1")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-rose-500/50 font-bold">✕</span> {t("landing.generic2")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-rose-500/50 font-bold">✕</span> {t("landing.generic3")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-rose-500/50 font-bold">✕</span> {t("landing.generic4")}
                  </li>
                </ul>
              </div>
              
              <div className="bg-white/[0.02] p-8 md:p-12">
                <div className="mb-6 inline-flex items-center rounded bg-white px-2.5 py-1 text-xs font-medium text-black uppercase tracking-widest">
                  SystemForge
                </div>
                <h3 className="text-lg font-medium text-white/90">{t("landing.sfWorkflow")}</h3>
                <ul className="mt-6 space-y-5 text-sm text-white/70 font-medium">
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-emerald-400 font-bold">✓</span> {t("landing.sf1")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-emerald-400 font-bold">✓</span> {t("landing.sf2")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-emerald-400 font-bold">✓</span> {t("landing.sf3")}
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="mt-0.5 text-emerald-400 font-bold">✓</span> {t("landing.sf4")}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>
      </section>
    </main>
  );
}
