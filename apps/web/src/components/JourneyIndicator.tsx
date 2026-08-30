"use client";

import React from "react";
import { LearnerAppStateResponse } from "../lib/types";

interface JourneyIndicatorProps {
  appState: LearnerAppStateResponse | null;
  activeTab?: string;
  onNavigateTab: (tab: string) => void;
}

export function JourneyIndicator({
  appState,
  onNavigateTab,
}: JourneyIndicatorProps) {
  if (!appState) return null;

  const stage = appState.stage;

  function getStepStatus(stepNum: number) {
    let currentStep = 1;
    if (stage === "GOAL_REQUIRED") currentStep = 1;
    else if (stage === "DIAGNOSTIC_REQUIRED" || stage === "DIAGNOSTIC_IN_PROGRESS") currentStep = 2;
    else if (stage === "PATH_SELECTION" || stage === "ACTIVE_LEARNING") currentStep = 3;
    else if (stage === "PROOF_REQUIRED") currentStep = 4;
    else if (stage === "ADAPTIVE_CONTINUATION") currentStep = 5;

    if (stepNum < currentStep) return "completed";
    if (stepNum === currentStep) return "active";
    return "upcoming";
  }

  const steps = [
    { num: 1, label: "01 Goal", tab: "goal" },
    { num: 2, label: "02 Diagnose", tab: "diagnostic" },
    { num: 3, label: "03 Learn", tab: "path" },
    { num: 4, label: "04 Prove", tab: "proof" },
    { num: 5, label: "05 Adapt", tab: "overview" },
  ];

  return (
    <div className="bg-surface/80 border border-subtle rounded-2xl p-4 shadow-xs mb-6 backdrop-blur-xs">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {steps.map((step) => {
            const status = getStepStatus(step.num);
            return (
              <button
                key={step.num}
                onClick={() => onNavigateTab(step.tab)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-180 whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary ${
                  status === "active"
                    ? "bg-accent-primary text-white shadow-xs"
                    : status === "completed"
                    ? "bg-accent-mint-subtle text-accent-mint border border-accent-mint/30 hover:opacity-90"
                    : "bg-subtle/50 text-secondary hover:text-primary hover:bg-subtle"
                }`}
              >
                <span>{step.label}</span>
                {status === "completed" && <span>✓</span>}
              </button>
            );
          })}
        </div>

        {/* Primary Recommended Action Banner */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-end border-t sm:border-t-0 border-subtle pt-2 sm:pt-0">
          <span className="text-[11px] font-bold uppercase tracking-wider text-secondary hidden md:inline">
            Recommended Action:
          </span>
          <button
            onClick={() => onNavigateTab(appState.next_action_route)}
            className="px-4 py-2 bg-accent-primary hover:opacity-90 text-white font-bold text-xs rounded-xl shadow-xs transition-all duration-180 flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
          >
            <span>{appState.next_action_label}</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
