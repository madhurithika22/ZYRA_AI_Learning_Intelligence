"use client";

import React from "react";
import { BottleneckAnalysisResponse } from "../lib/types";
import { Button } from "./ui/Button";

interface BottleneckViewProps {
  bottleneckData: BottleneckAnalysisResponse | null;
  loading: boolean;
  onRefresh?: () => void;
  onBackToOverview?: () => void;
  onNavigateToPath?: () => void;
}

export function BottleneckView({
  bottleneckData,
  loading,
  onBackToOverview,
  onNavigateToPath,
}: BottleneckViewProps) {
  if (loading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="inline-block animate-spin h-8 w-8 text-accent-primary border-4 border-current border-t-transparent rounded-full" />
        <p className="text-secondary text-sm">Analyzing skill gaps and dependency graphs...</p>
      </div>
    );
  }

  if (!bottleneckData || !bottleneckData.primary_bottleneck) {
    return (
      <div className="bg-surface border border-subtle rounded-3xl p-12 text-center max-w-2xl mx-auto space-y-6 shadow-xs">
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Skill Competency Map
          </span>
          <h3 className="text-3xl font-extrabold text-primary">YOUR SKILL MAP</h3>
          <p className="text-secondary text-sm max-w-md mx-auto leading-relaxed">
            Your skill map and primary bottleneck rankings will take shape during the diagnostic check.
          </p>
        </div>
      </div>
    );
  }

  const primary = bottleneckData.primary_bottleneck;

  return (
    <div className="space-y-12 py-4">
      {onBackToOverview && (
        <button
          type="button"
          onClick={onBackToOverview}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
        >
          <span>←</span>
          <span>Back to Overview</span>
        </button>
      )}

      {/* Large Editorial Insight Card */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-secondary">
            YOUR CURRENT BOTTLENECK
          </span>
          <h1 className="text-3xl md:text-5xl font-extrabold text-primary tracking-tight">
            {primary.skill_name}
          </h1>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-1">
            <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
              Skill Gap
            </div>
            <div className="text-3xl font-extrabold text-accent-secondary">
              {Math.round(primary.gap * 100)}%
            </div>
          </div>

          <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-1">
            <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
              Evidence Confidence
            </div>
            <div className="text-3xl font-extrabold text-accent-mint">
              {Math.round(primary.confidence * 100)}%
            </div>
          </div>

          <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-1">
            <div className="text-xs font-semibold text-secondary uppercase tracking-wider">
              Dependency Impact
            </div>
            <div className="text-3xl font-extrabold text-accent-primary">
              {primary.dependency_impact.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wider">Why is this a Bottleneck?</h3>
          <p className="text-secondary text-sm leading-relaxed max-w-3xl">
            {primary.explanation.primary_reason}
          </p>
        </div>
      </div>

      {/* Ranked Skill Gaps Table */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-extrabold text-primary">Ranked Target Role Skill Gaps</h3>
          <span className="text-xs text-secondary">{bottleneckData.all_gaps.length} Evaluated Gaps</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-primary">
            <thead className="border-b border-subtle text-secondary uppercase text-[11px] font-semibold tracking-wider">
              <tr>
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Skill Name</th>
                <th className="py-3 px-4">Demonstrated</th>
                <th className="py-3 px-4">Required</th>
                <th className="py-3 px-4">Bottleneck Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {bottleneckData.all_gaps.map((gap) => (
                <tr key={gap.skill_id} className="hover:bg-subtle/30 transition-colors">
                  <td className="py-4 px-4 font-bold text-secondary">#{gap.rank}</td>
                  <td className="py-4 px-4 font-semibold text-primary">{gap.skill_name}</td>
                  <td className="py-4 px-4 text-accent-secondary font-bold">
                    {Math.round(gap.mastery * 100)}%
                  </td>
                  <td className="py-4 px-4 text-secondary">{Math.round(gap.required_level * 100)}%</td>
                  <td className="py-4 px-4 font-extrabold text-accent-primary">
                    {gap.bottleneck_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {onNavigateToPath && (
          <div className="pt-4 border-t border-subtle flex justify-end">
            <Button variant="primary" size="lg" onClick={onNavigateToPath}>
              Build My Learning Path →
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
