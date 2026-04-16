"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { signInSchema } from "@/features/auth/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { useI18n } from "@/i18n/i18n-context";
import { z } from "zod";

type FormData = z.infer<typeof signInSchema>;

export default function SignInPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const { t } = useI18n();
  const [error, setError] = useState("");
  const form = useForm<FormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: "", password: "" },
    mode: "onBlur",
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError("");
    try {
      await signIn(values);
      router.push("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
    }
  });

  return (
    <AuthShell title={t("auth.signInTitle")} subtitle={t("auth.signInSubtitle")}>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <Label htmlFor="email">{t("auth.email")}</Label>
          <Input id="email" placeholder={t("auth.emailPlaceholder")} {...form.register("email")} />
          {form.formState.errors.email ? (
            <p className="text-xs text-red-400">{form.formState.errors.email.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">{t("auth.password")}</Label>
          <Input id="password" type="password" placeholder="••••••••" {...form.register("password")} />
          {form.formState.errors.password ? (
            <p className="text-xs text-red-400">{form.formState.errors.password.message}</p>
          ) : null}
        </div>
        {error ? <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">{error}</p> : null}
        <Button type="submit" className="w-full bg-white text-black hover:bg-white/90 font-medium" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? t("auth.signingIn") : t("common.signIn")}
        </Button>
      </form>
      <p className="mt-5 text-sm text-white/50 text-center font-light">
        {t("auth.noAccount")}{" "}
        <Link className="font-medium text-white hover:text-white/80 underline-offset-4 hover:underline" href="/auth/sign-up">
          {t("auth.createOne")}
        </Link>
      </p>
    </AuthShell>
  );
}
