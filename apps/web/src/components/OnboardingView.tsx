"use client";

import React, { useState } from "react";
import { AuthUser } from "../lib/types";
import { updateLearnerProfile } from "../lib/api";
import { Button } from "./ui/Button";

interface OnboardingViewProps {
  user: AuthUser;
  onComplete: () => void;
}

export function OnboardingView({ user, onComplete }: OnboardingViewProps) {
  const [background, setBackground] = useState("intermediate");
  const [dailyTime, setDailyTime] = useState("60");

  const steps = [
    { num: "01", label: "Profile", active: true },
    { num: "02", label: "Goal", active: false },
    { num: "03", label: "Diagnose", active: false },
    { num: "04", label: "Your Path", active: false },
  ];

  const [submitting, setSubmitting] = useState(false);

  async function handleContinue() {
    setSubmitting(true);
    try {
      await updateLearnerProfile(user.learner_id, {
        experience_level: background === "beginner" ? "Beginner" : background === "advanced" ? "Advanced" : "Intermediate",
        weekly_availability_hours: Math.round((Number(dailyTime) * 7) / 60),
      });
    } catch {
      // Continue even if initial profile write encounters minor warning
    } finally {
      setSubmitting(false);
      onComplete();
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-12 space-y-10">
      {/* Calm Step Progression Indicator */}
      <div className="flex items-center justify-between border-b border-subtle pb-6">
        {steps.map((step) => (
          <div key={step.num} className="flex items-center space-x-3">
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full ${
                step.active
                  ? "bg-accent-primary text-white"
                  : "bg-subtle text-secondary"
              }`}
            >
              {step.num}
            </span>
            <span
              className={`text-xs font-medium ${
                step.active ? "text-primary font-bold" : "text-secondary"
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>

      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs space-y-8">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Welcome {user.display_name}
          </span>
          <h2 className="text-3xl font-extrabold text-primary tracking-tight">
            Let&apos;s build your learning profile
          </h2>
          <p className="text-secondary text-sm">
            Tell us about your background so we can configure your adaptive baseline.
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
              What is your current technical background?
            </label>
            <select
              value={background}
              onChange={(e) => setBackground(e.target.value)}
              className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary transition-all"
            >
              <option value="beginner">Beginner (New to software engineering)</option>
              <option value="intermediate">Intermediate (Know Python / basic web development)</option>
              <option value="advanced">Advanced (Experienced software engineer)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
              How much time can you study daily?
            </label>
            <select
              value={dailyTime}
              onChange={(e) => setDailyTime(e.target.value)}
              className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary transition-all"
            >
              <option value="30">30 Minutes / Day</option>
              <option value="60">60 Minutes / Day</option>
              <option value="90">90 Minutes / Day</option>
              <option value="120">2+ Hours / Day</option>
            </select>
          </div>
        </div>

        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={submitting}
          onClick={handleContinue}
        >
          {submitting ? "Saving Profile..." : "Continue to Goal Setup →"}
        </Button>
      </div>
    </div>
  );
}
