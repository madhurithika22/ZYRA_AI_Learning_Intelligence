"use client";

import React from "react";
import { LearningTwinResponse } from "../lib/types";
import { Button } from "./ui/Button";

interface NextActionViewProps {
  twinData: LearningTwinResponse | null;
  onExecuteAction: () => void;
}

export function NextActionView({ twinData, onExecuteAction }: NextActionViewProps) {
  const nextAction = twinData?.next_best_action;

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-10">
      {/* Visually Dominant Next Best Action Card */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            RECOMMENDED INTERVENTION
          </span>
          <h1 className="text-3xl md:text-5xl font-extrabold text-primary tracking-tight">
            NEXT BEST ACTION
          </h1>
        </div>

        <div className="bg-accent-primary-subtle border border-accent-primary/30 rounded-2xl p-8 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-2xl font-extrabold text-primary">
              {nextAction?.skill_name || "Prerequisite Review: Docker"}
            </h2>
            <span className="px-3.5 py-1.5 rounded-full bg-accent-primary-subtle text-accent-primary text-xs font-bold border border-accent-primary/30">
              {nextAction?.estimated_minutes || 45} Mins
            </span>
          </div>

          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
              Why this now?
            </h3>
            <p className="text-sm text-secondary leading-relaxed">
              {nextAction?.rationale ||
                "Resolving this prerequisite unlocks downstream dependencies for Model Deployment and MLOps nodes."}
            </p>
          </div>

          <Button variant="primary" size="lg" onClick={onExecuteAction}>
            Start Next Action →
          </Button>
        </div>
      </div>

      {/* Alternative Recommendations */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 shadow-xs space-y-6">
        <h3 className="text-lg font-bold text-primary">Alternative Interventions</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-3">
            <h4 className="text-base font-bold text-primary">Diagnostic Refinement Check</h4>
            <p className="text-xs text-secondary leading-relaxed">
              Answer 3 targeted diagnostic questions on Statistics to increase state confidence.
            </p>
          </div>

          <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-3">
            <h4 className="text-base font-bold text-primary">PyTorch Foundations Review</h4>
            <p className="text-xs text-secondary leading-relaxed">
              Complete low-effort tensor manipulation coding exercise.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
