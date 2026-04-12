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
import { register } from "@/features/auth/service";
import { signUpSchema } from "@/features/auth/schemas";
import { useAuth } from "@/features/auth/auth-context";
import { useI18n } from "@/i18n/i18n-context";
import { z } from "zod";

type FormData = z.infer<typeof signUpSchema>;

export default function SignUpPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const { t } = useI18n();
  const [error, setError] = useState("");
  const form = useForm<FormData>({
    resolver: zodResolver(signUpSchema),
    defaultValues: { full_name: "", email: "", password: "" },
    mode: "onBlur",
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError("");
    try {
      await register(values);
      await signIn({ email: values.email, password: values.password });
      router.push("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    }
  });

  return (
    <AuthShell
      title={t("auth.signUpTitle")}
      subtitle={t("auth.signUpSubtitle")}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <Label htmlFor="full_name">Full Name</Label>
          <Input id="full_name" placeholder="Ada Lovelace" {...form.register("full_name")} />
          {form.formState.errors.full_name ? (
            <p className="text-xs text-red-400">{form.formState.errors.full_name.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" placeholder="name@company.com" {...form.register("email")} />
          {form.formState.errors.email ? (
            <p className="text-xs text-red-400">{form.formState.errors.email.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" placeholder="At least 8 chars, mixed case, number" {...form.register("password")} />
          {form.formState.errors.password ? (
            <p className="text-xs text-red-400">{form.formState.errors.password.message}</p>
          ) : null}
        </div>
        {error ? <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">{error}</p> : null}
        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? t("auth.creatingAccount") : t("auth.createOne")}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted">
        {t("auth.haveAccount")}{" "}
        <Link className="font-medium text-brand hover:underline" href="/auth/sign-in">
          {t("common.signIn")}
        </Link>
      </p>
    </AuthShell>
  );
}
