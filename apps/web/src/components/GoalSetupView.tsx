"use client";

import React, { useState } from "react";
import { interpretGoal, saveGoal } from "../lib/api";
import { AuthUser, GoalIntelligenceResult } from "../lib/types";
import { formatApiError } from "../lib/formatError";
import { Button } from "./ui/Button";

interface GoalSetupViewProps {
  user: AuthUser;
  onGoalSaved: (goalId: string) => void;
  onStartDiagnostic: (goalId: string) => void;
  onBackToProfile?: () => void;
}

export function GoalSetupView({
  user,
  onGoalSaved,
  onStartDiagnostic,
  onBackToProfile,
}: GoalSetupViewProps) {

  const [goalPrompt, setGoalPrompt] = useState(
    "I want to become a Machine Learning Engineer in 6 months. I know Python and basic calculus, and can study 90 minutes a day."
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GoalIntelligenceResult | null>(null);

  const [saving, setSaving] = useState(false);
  const [savedGoalId, setSavedGoalId] = useState<string | null>(null);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await interpretGoal(goalPrompt);
      setResult(data);
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await saveGoal(user.learner_id, goalPrompt);
      setSavedGoalId(res.goal_id);
      onGoalSaved(res.goal_id);
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-10">
      {onBackToProfile && (
        <button
          type="button"
          onClick={onBackToProfile}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
        >
          <span>←</span>
          <span>Back to Profile</span>
        </button>
      )}

      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs space-y-8">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Goal Intelligence
          </span>
          <h2 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight">
            What do you want to become?
          </h2>
          <p className="text-secondary text-sm">
            Describe your goal naturally. We&apos;ll turn it into a structured learning objective.
          </p>
        </div>

        <textarea
          rows={4}
          value={goalPrompt}
          onChange={(e) => setGoalPrompt(e.target.value)}
          placeholder="E.g., I want to become an AI Engineer in 6 months..."
          className="w-full bg-subtle/50 border border-subtle rounded-2xl p-5 text-sm text-primary placeholder-muted focus:outline-none focus:border-accent-primary transition-all leading-relaxed"
        />

        {error && (
          <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-2xl p-4 text-xs font-medium text-accent-rose">
            {error}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-4">
          <Button
            variant="primary"
            size="lg"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing your goal..." : "Analyze My Goal"}
          </Button>

          {result && !savedGoalId && (
            <Button
              variant="secondary"
              size="lg"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Saving Goal..." : "Save Goal to Profile"}
            </Button>
          )}
        </div>

        {savedGoalId && (
          <div className="bg-accent-mint-subtle border border-accent-mint/30 rounded-2xl p-6 text-sm text-accent-mint flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="font-extrabold text-base block">Your goal is ready.</span>
              <span className="text-xs text-secondary mt-0.5 block">
                Persisted to your authenticated profile database. Start your adaptive check next.
              </span>
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={() => onStartDiagnostic(savedGoalId)}
            >
              Start Adaptive Diagnostic →
            </Button>
          </div>
        )}
      </div>

      {/* Structured Goal Review Card */}
      {result && (
        <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs space-y-8">
          <div className="flex items-center justify-between border-b border-subtle pb-4">
            <h3 className="text-xl font-extrabold text-primary">Structured Goal Review</h3>
            <span className="text-xs px-3 py-1 rounded-full bg-subtle text-accent-primary font-semibold">
              Confidence: {Math.round(result.interpretation.confidence * 100)}%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-subtle/40 border border-subtle p-5 rounded-2xl space-y-1">
              <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
                Target Role
              </div>
              <div className="text-lg font-extrabold text-accent-primary">
                {result.resolved_role.canonical_role_name || "Custom Target"}
              </div>
            </div>

            <div className="bg-subtle/40 border border-subtle p-5 rounded-2xl space-y-1">
              <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
                Timeline
              </div>
              <div className="text-lg font-extrabold text-accent-sky">
                {result.interpretation.timeline_weeks || 26} Weeks
              </div>
            </div>

            <div className="bg-subtle/40 border border-subtle p-5 rounded-2xl space-y-1">
              <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
                Daily Commitment
              </div>
              <div className="text-lg font-extrabold text-accent-mint">
                {result.interpretation.daily_minutes || 60} Min/Day
              </div>
            </div>
          </div>

          {/* Explicit Facts vs AI Interpretation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                Learner Stated Skills
              </span>
              <div className="flex flex-wrap gap-2">
                {result.resolved_skills.resolved_skills.length > 0 ? (
                  result.resolved_skills.resolved_skills.map((s) => (
                    <span
                      key={s.skill_id}
                      className="px-3 py-1.5 rounded-xl bg-subtle text-primary text-xs font-semibold"
                    >
                      {s.name}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-muted">No prior skills declared</span>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                Identified Constraints
              </span>
              <div className="flex flex-wrap gap-2">
                {result.interpretation.constraints.length > 0 ? (
                  result.interpretation.constraints.map((c, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 rounded-xl bg-accent-amber-subtle text-accent-secondary text-xs font-medium border border-accent-amber/30"
                    >
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-muted">None specified</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
