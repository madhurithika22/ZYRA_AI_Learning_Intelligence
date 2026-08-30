"use client";

import React, { useState } from "react";
import { loginUser, fetchCurrentAuthUser } from "../lib/api";
import { AuthUser } from "../lib/types";

interface SignInViewProps {
  onSuccess: (user: AuthUser, nextTab?: string) => void;
  onSwitchSignUp: () => void;
  onBackToLanding: () => void;
}

export function SignInView({
  onSuccess,
  onSwitchSignUp,
  onBackToLanding,
}: SignInViewProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validateEmail(emailStr: string): boolean {
    return /^\S+@\S+\.\S+$/.test(emailStr.trim());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGeneralError(null);

    const errors: { email?: string; password?: string } = {};

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      errors.email = "Email address is required.";
    } else if (!validateEmail(cleanEmail)) {
      errors.email = "Please enter a valid email address.";
    }

    if (!password) {
      errors.password = "Password is required.";
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setGeneralError("Please check the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setSubmitting(true);

    try {
      // 1. Send Login Request
      await loginUser(cleanEmail, password);

      // 2. Strictly confirm session via GET /api/v1/auth/me
      const confirmedUser = await fetchCurrentAuthUser();
      if (confirmedUser) {
        onSuccess(confirmedUser, "overview");
      } else {
        setGeneralError("Unable to sign in. Check your email and password and try again.");
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);

      // Sanitized Error Mapping: NEVER expose backend internals, DB details, stack traces, or UUIDs
      if (
        errMsg.toLowerCase().includes("failed to fetch") ||
        errMsg.toLowerCase().includes("networkerror") ||
        errMsg.toLowerCase().includes("failed to connect") ||
        errMsg.toLowerCase().includes("fetch failed")
      ) {
        setGeneralError("We couldn't reach the service. Please try again.");
      } else {
        setGeneralError("Unable to sign in. Check your email and password and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-md mx-auto py-6 sm:py-10 px-4">
      {/* Back to landing button */}
      <button
        type="button"
        onClick={onBackToLanding}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary mb-4 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-lg px-2 py-1"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>Back to landing</span>
      </button>

      {/* Surface Card */}
      <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 md:p-10 shadow-lg space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-accent-primary">
            ADAPTIVE LEARNING INTELLIGENCE
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-primary tracking-tight">
            Welcome back.
          </h2>
          <p className="text-xs sm:text-sm text-secondary leading-relaxed">
            Continue your adaptive learning journey.
          </p>
        </div>

        {/* General Error Alert Box */}
        {generalError && (
          <div
            role="alert"
            aria-live="polite"
            className="bg-accent-rose/10 border border-accent-rose/20 rounded-2xl p-4 text-xs font-medium text-accent-rose flex items-start gap-2.5"
          >
            <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{generalError}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label
              htmlFor="signin-email"
              className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2"
            >
              Email Address
            </label>
            <input
              id="signin-email"
              type="email"
              required
              disabled={submitting}
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }));
              }}
              placeholder="name@example.com"
              className={`w-full bg-subtle/50 border ${
                fieldErrors.email ? "border-accent-rose focus:border-accent-rose" : "border-subtle focus:border-accent-primary"
              } rounded-2xl px-4 py-3.5 text-sm text-primary placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/20 transition-all disabled:opacity-50`}
            />
            {fieldErrors.email && (
              <p className="text-[11px] font-medium text-accent-rose mt-1 px-1">{fieldErrors.email}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="signin-password"
              className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="signin-password"
                type={showPassword ? "text" : "password"}
                required
                disabled={submitting}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="••••••••"
                className={`w-full bg-subtle/50 border ${
                  fieldErrors.password ? "border-accent-rose focus:border-accent-rose" : "border-subtle focus:border-accent-primary"
                } rounded-2xl pl-4 pr-12 py-3.5 text-sm text-primary placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent-primary/20 transition-all disabled:opacity-50`}
              />
              <button
                type="button"
                disabled={submitting}
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-secondary hover:text-primary transition-colors p-1 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {fieldErrors.password && (
              <p className="text-[11px] font-medium text-accent-rose mt-1 px-1">{fieldErrors.password}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-4 rounded-2xl bg-accent-primary hover:opacity-90 text-white font-bold text-sm shadow-md transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                <span>Signing you in…</span>
              </>
            ) : (
              <span>Sign In →</span>
            )}
          </button>
        </form>

        {/* Switch to Sign Up */}
        <div className="text-center text-xs text-secondary pt-2 border-t border-subtle">
          Don&apos;t have an account?{" "}
          <button
            type="button"
            onClick={onSwitchSignUp}
            className="text-accent-primary hover:underline font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded px-1"
          >
            Create one →
          </button>
        </div>
      </div>
    </div>
  );
}
