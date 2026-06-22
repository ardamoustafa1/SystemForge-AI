"use client";

import { useI18n } from "@/i18n/i18n-context";
import { motion } from "framer-motion";
import { Cpu, Zap, Shield, GitMerge, Layout, Blocks } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

export default function FeaturesPage() {
  const { t } = useI18n();

  const features = [
    {
      icon: <Cpu className="w-6 h-6 text-brand" />,
      title: "AI-Driven Architecture Generation",
      description:
        "Convert basic product requirements into complex, production-ready system architectures instantly using advanced LLMs.",
    },
    {
      icon: <Zap className="w-6 h-6 text-blue-500" />,
      title: "Real-Time Collaboration",
      description:
        "Design alongside your engineering team with multi-player presence, live cursor tracking, and instant updates via Redis Streams.",
    },
    {
      icon: <Blocks className="w-6 h-6 text-purple-500" />,
      title: "Interactive Artifacts",
      description:
        "Interact with generated diagrams, explore component dependencies, and manipulate the system topology directly in the browser.",
    },
    {
      icon: <GitMerge className="w-6 h-6 text-green-500" />,
      title: "Automated Export Pipelines",
      description:
        "Instantly export your architecture into Markdown documentation, Mermaid charts, or Terraform structural outlines.",
    },
    {
      icon: <Shield className="w-6 h-6 text-red-500" />,
      title: "Enterprise Grade Security",
      description:
        "Built on a zero-trust model with RBAC, secure API gateways, and fully isolated workspace partitions for each tenant.",
    },
    {
      icon: <Layout className="w-6 h-6 text-orange-500" />,
      title: "Premium Developer Experience",
      description:
        "A gorgeous, responsive interface crafted with Tailwind and Framer Motion that makes complex system design feel effortless.",
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300 } },
  };

  return (
    <div className="container-page py-16 relative">
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-brand/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 left-1/4 w-[30rem] h-[30rem] bg-purple-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-3xl mx-auto text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70">
          Supercharge Your Engineering Workflow
        </h1>
        <p className="text-lg text-muted">
          SystemForge AI brings everything you need to transition from idea to
          scalable architecture in minutes, not months.
        </p>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8"
      >
        {features.map((feature, idx) => (
          <motion.div
            key={idx}
            variants={itemVariants}
            className="group p-6 rounded-2xl glass-card border border-border/40 hover:border-brand/40 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-brand/5 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="w-12 h-12 bg-background/50 rounded-xl border border-border/50 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
              {feature.icon}
            </div>
            <h3 className="text-xl font-semibold mb-3 group-hover:text-brand transition-colors duration-300">
              {feature.title}
            </h3>
            <p className="text-sm text-muted leading-relaxed">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
