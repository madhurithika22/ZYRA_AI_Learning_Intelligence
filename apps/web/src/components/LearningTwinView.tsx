"use client";

import React from "react";
import { LearningTwinResponse } from "../lib/types";
import { Button } from "./ui/Button";

interface LearningTwinViewProps {
  twinData: LearningTwinResponse | null;
  loading: boolean;
  error: string | null;
  onNavigateTab: (tab: string) => void;
}

export function LearningTwinView({
  twinData,
  loading,
  error,
  onNavigateTab,
}: LearningTwinViewProps) {
  if (loading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="inline-block animate-spin h-8 w-8 text-accent-primary border-4 border-current border-t-transparent rounded-full" />
        <p className="text-secondary text-sm">Assembling Learning Twin computational state...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-3xl p-8 text-center space-y-4 max-w-xl mx-auto">
        <h3 className="text-lg font-bold text-accent-rose">Failed to load Learning Twin</h3>
        <p className="text-xs text-secondary">{error}</p>
      </div>
    );
  }

  if (!twinData || !twinData.goal) {
    return (
      <div className="bg-surface border border-subtle rounded-3xl p-12 text-center max-w-xl mx-auto space-y-6 shadow-xs">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Profile Empty
          </span>
          <h3 className="text-2xl font-extrabold text-primary">No active goal configured</h3>
          <p className="text-secondary text-sm">
            Create your first target goal to compute your skills, bottleneck, and adaptive path.
          </p>
        </div>
        <Button
          variant="primary"
          size="lg"
          onClick={() => onNavigateTab("goal")}
        >
          Create Learning Goal →
        </Button>
      </div>
    );
  }

  const skillList = twinData.skills || twinData.goal_skills || [];
  const progressPct = Math.round(
    (twinData.goal?.goal_skill_progress ?? twinData.overall_progress?.weighted_goal_progress ?? 0) * 100
  );
  const targetRole = twinData.goal?.target_role_name || twinData.goal?.objective || "Active Learning Goal";
  const confidenceLevel =
    typeof twinData.state_confidence === "object"
      ? twinData.state_confidence?.level || "HIGH"
      : twinData.state_confidence || "HIGH";

  const bottleneckName =
    twinData.bottleneck?.skill_name || twinData.primary_bottleneck?.skill_name || "Diagnostic Check Required";
  const bottleneckReason =
    twinData.bottleneck?.reason ||
    twinData.primary_bottleneck?.explanation?.primary_reason ||
    "Complete your diagnostic assessment to identify your key skill constraint.";

  const nextActionTitle =
    twinData.next_action?.title ||
    twinData.next_action?.target_skill_name ||
    twinData.next_best_action?.skill_name ||
    "Complete Diagnostic Check";
  const nextActionReason =
    twinData.next_action?.primary_reason ||
    twinData.next_best_action?.rationale ||
    "Targeted intervention designed to resolve your highest-impact skill gap.";

  return (
    <div className="space-y-12 py-4">
      {/* Editorial Hero Header */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-subtle pb-6">
          <div className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
              YOUR LEARNING STATE
            </span>
            <h1 className="text-3xl md:text-5xl font-extrabold text-primary tracking-tight">
              {targetRole}
            </h1>
          </div>

          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-xs text-secondary uppercase font-semibold">Goal Progress</div>
              <div className="text-3xl font-extrabold text-accent-primary">{progressPct}%</div>
            </div>

            <div className="text-right pl-6 border-l border-subtle">
              <div className="text-xs text-secondary uppercase font-semibold">State Confidence</div>
              <div className="text-sm font-extrabold text-accent-mint uppercase mt-1">
                {confidenceLevel}
              </div>
            </div>
          </div>
        </div>

        {/* Visually Prominent Highlights: Bottleneck & Next Best Action */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Bottleneck */}
          <div className="bg-accent-amber-subtle border border-accent-amber/30 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-secondary">
                CURRENT BOTTLENECK
              </span>
              <button
                onClick={() => onNavigateTab("skills")}
                className="text-xs font-semibold text-accent-secondary hover:underline"
              >
                Deep-dive →
              </button>
            </div>
            <div className="text-2xl font-extrabold text-primary">
              {bottleneckName}
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              {bottleneckReason}
            </p>
          </div>

          {/* Next Best Action */}
          <div className="bg-accent-primary-subtle border border-accent-primary/30 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                NEXT BEST ACTION
              </span>
              <button
                onClick={() => onNavigateTab("path")}
                className="text-xs font-semibold text-accent-primary hover:underline"
              >
                View Path →
              </button>
            </div>
            <div className="text-2xl font-extrabold text-primary">
              {nextActionTitle}
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              {nextActionReason}
            </p>
          </div>
        </div>
      </div>

      {/* Goal Skill Matrix Table */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-extrabold text-primary">Goal Skill Matrix</h3>
          <span className="text-xs text-secondary">
            {skillList.length} Required Competencies
          </span>
        </div>

        {skillList.length === 0 ? (
          <div className="bg-subtle/30 border border-subtle rounded-2xl p-6 text-center space-y-2">
            <p className="text-xs text-secondary">
              No skill matrix records found yet. Complete your diagnostic check to evaluate skill competencies.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-primary">
              <thead className="border-b border-subtle text-secondary uppercase text-[11px] font-semibold tracking-wider">
                <tr>
                  <th className="py-3 px-4">Skill Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Demonstrated Mastery</th>
                  <th className="py-3 px-4">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-subtle">
                {skillList.map((skill) => {
                  const masteryVal = skill.mastery ?? skill.mastery_score ?? 0;
                  const confVal = skill.confidence ?? 0;
                  return (
                    <tr key={skill.skill_id} className="hover:bg-subtle/30 transition-colors">
                      <td className="py-4 px-4 font-semibold text-primary">{skill.skill_name}</td>
                      <td className="py-4 px-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-subtle text-secondary border border-subtle uppercase">
                          {skill.status || "Target"}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-24 bg-subtle h-2 rounded-full overflow-hidden">
                            <div
                              className="bg-accent-primary h-full rounded-full"
                              style={{ width: `${Math.round(masteryVal * 100)}%` }}
                            />
                          </div>
                          <span className="font-bold text-accent-primary">
                            {Math.round(masteryVal * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-secondary">
                        {Math.round(confVal * 100)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
