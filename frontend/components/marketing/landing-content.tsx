"use client";

import Link from "next/link";
import { motion } from "framer-motion";

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
    <main>
      <section className="container-page py-20 sm:py-24">
        <motion.div className="mx-auto max-w-4xl text-center" {...riseIn}>
          <p className="mx-auto mb-5 inline-flex rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted">
            {t("landing.badge")}
          </p>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
            {t("landing.heroTitle1")}
            <span className="block text-brand">{t("landing.heroTitle2")}</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base text-muted sm:text-lg">
            {t("landing.heroDesc")}
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link href="/auth/sign-up">
              <Button className="h-11 px-6">{t("landing.ctaPrimary")}</Button>
            </Link>
            <Link href="/auth/sign-in">
              <Button variant="outline" className="h-11 px-6">
                {t("landing.ctaSecondary")}
              </Button>
            </Link>
          </div>
        </motion.div>

        <motion.div className="mx-auto mt-14 max-w-5xl" {...riseIn}>
          <Card className="overflow-hidden border-border/80 bg-gradient-to-br from-surface to-black/40 p-0">
            <div className="border-b border-border px-5 py-3 text-xs text-muted">{t("landing.sample")}</div>
            <div className="grid gap-6 p-6 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-medium">{t("landing.archSummary")}</h3>
                <p className="mt-2 text-sm text-muted">
                  {t("landing.sampleSummaryText")}
                </p>
                <h3 className="mt-5 text-sm font-medium">{t("landing.topTradeoff")}</h3>
                <p className="mt-2 text-sm text-muted">{t("landing.topTradeoffText")}</p>
              </div>
              <div className="rounded-lg border border-border bg-black/30 p-4 text-xs text-muted">
                <p>{t("landing.scorecard")}</p>
                <p className="mt-2">Scalability: 8/10</p>
                <p>Reliability: 7/10</p>
                <p>Security: 8/10</p>
                <p>Maintainability: 8/10</p>
                <p>Cost Efficiency: 8/10</p>
                <p>Simplicity: 7/10</p>
              </div>
            </div>
          </Card>
        </motion.div>
      </section>

      <section id="features" className="container-page py-14">
        <motion.div {...riseIn}>
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t("landing.featuresTitle")}</h2>
          <p className="mt-3 max-w-2xl text-sm text-muted sm:text-base">
            {t("landing.featuresSubtitle")}
          </p>
        </motion.div>
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div key={feature.titleKey} {...riseIn} transition={{ ...riseIn.transition, delay: index * 0.03 }}>
              <Card className="h-full p-5">
                <h3 className="text-base font-medium">{t(feature.titleKey)}</h3>
                <p className="mt-2 text-sm text-muted">{t(feature.descKey)}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="use-cases" className="container-page py-14">
        <motion.div {...riseIn}>
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t("landing.useCasesTitle")}</h2>
          <p className="mt-3 text-sm text-muted sm:text-base">{t("landing.useCasesSubtitle")}</p>
        </motion.div>
        <div className="mt-8 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {useCases.map((item, index) => (
            <motion.div key={item} {...riseIn} transition={{ ...riseIn.transition, delay: index * 0.02 }}>
              <Card className="p-4 text-sm">{t(item)}</Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="comparison" className="container-page py-14">
        <motion.div {...riseIn}>
          <Card className="overflow-hidden p-0">
            <div className="border-b border-border px-6 py-5">
              <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">{t("landing.whyNotTitle")}</h2>
              <p className="mt-2 text-sm text-muted">
                {t("landing.comparisonSubtitle")}
              </p>
            </div>
            <div className="grid md:grid-cols-2">
              <div className="border-b border-border p-6 md:border-b-0 md:border-r">
                <h3 className="font-medium">{t("landing.genericWorkflow")}</h3>
                <ul className="mt-3 space-y-2 text-sm text-muted">
                  <li>- {t("landing.generic1")}</li>
                  <li>- {t("landing.generic2")}</li>
                  <li>- {t("landing.generic3")}</li>
                  <li>- {t("landing.generic4")}</li>
                </ul>
              </div>
              <div className="p-6">
                <h3 className="font-medium">{t("landing.sfWorkflow")}</h3>
                <ul className="mt-3 space-y-2 text-sm text-muted">
                  <li>- {t("landing.sf1")}</li>
                  <li>- {t("landing.sf2")}</li>
                  <li>- {t("landing.sf3")}</li>
                  <li>- {t("landing.sf4")}</li>
                </ul>
              </div>
            </div>
          </Card>
        </motion.div>
      </section>
    </main>
  );
}
