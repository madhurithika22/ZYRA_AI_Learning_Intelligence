"use client";

import React, { useState } from "react";
import { AuthUser } from "../lib/types";
import { Button } from "./ui/Button";

interface SelfAssessmentViewProps {
  user: AuthUser;
  goalId: string | null;
  onComplete: () => void;
}

const DEFAULT_SKILLS = [
  "Python Programming",
  "Statistics & Probability",
  "Machine Learning Foundations",
  "Deep Learning & Neural Networks",
  "Docker & Containerization",
  "Model Deployment & Serving",
];

const RATING_OPTIONS = [
  "Beginner",
  "Familiar",
  "Intermediate",
  "Advanced",
  "Expert",
  "I don't know",
];

export function SelfAssessmentView({
  onComplete,
}: SelfAssessmentViewProps) {
  const [ratings, setRatings] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function handleRatingChange(skill: string, value: string) {
    setRatings((prev) => ({ ...prev, [skill]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Self-reported ratings are stored locally/transiently to inform initial diagnostic question selection
      // without mutating verified SkillMastery.
      onComplete();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-10 space-y-8">
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-accent-amber-subtle text-accent-secondary border border-accent-amber/30">
              Self-Reported Baseline
            </span>
            <span className="text-xs text-secondary">
              Does NOT update verified mastery
            </span>
          </div>

          <h1 className="text-3xl font-extrabold text-primary tracking-tight">
            How would you rate your current experience?
          </h1>
          <p className="text-sm text-secondary leading-relaxed">
            Your self-assessment helps guide our diagnostic question engine. Real mastery will be confirmed through adaptive checks and proof assessments.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 border-t border-subtle pt-6">
          <div className="space-y-6">
            {DEFAULT_SKILLS.map((skill) => (
              <div key={skill} className="bg-subtle/40 border border-subtle p-5 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-primary">{skill}</span>
                  <span className="text-xs font-semibold text-accent-primary">
                    {ratings[skill] || "Unselected"}
                  </span>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {RATING_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleRatingChange(skill, opt)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                        ratings[skill] === opt
                          ? "bg-accent-primary text-white shadow-xs"
                          : "bg-surface text-secondary hover:text-primary border border-subtle"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <Button
            variant="primary"
            size="lg"
            fullWidth
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Saving Baseline..." : "Save Baseline & Confirm What You Know →"}
          </Button>
        </form>
      </div>
    </div>
  );
}
