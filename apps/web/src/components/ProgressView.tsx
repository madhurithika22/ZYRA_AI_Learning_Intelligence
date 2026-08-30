"use client";

import React from "react";
import { LearningTwinResponse } from "../lib/types";

interface ProgressViewProps {
  twinData: LearningTwinResponse | null;
  onBackToOverview?: () => void;
  onNavigateNextAction?: () => void;
}

export function ProgressView({ twinData, onBackToOverview }: ProgressViewProps) {

  if (!twinData || !twinData.goal) {
    return (
      <div className="bg-surface border border-subtle rounded-3xl p-12 text-center max-w-2xl mx-auto space-y-6 shadow-xs">
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Longitudinal Tracker
          </span>
          <h3 className="text-3xl font-extrabold text-primary">YOUR PROGRESS WILL APPEAR HERE</h3>
          <p className="text-secondary text-sm max-w-md mx-auto leading-relaxed">
            Once you complete your diagnostic and begin learning, this space will track your mastery, evidence confidence, skill growth, and path completion.
          </p>
        </div>
      </div>
    );
  }

  const skillList = twinData.skills || twinData.goal_skills || [];
  const overallProgressPct = Math.round(
    (twinData.goal?.goal_skill_progress ?? twinData.overall_progress?.weighted_goal_progress ?? 0) * 100
  );
  const targetRole = twinData.goal?.target_role_name || twinData.goal?.objective || "Active Learning Goal";

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

      {/* Large Progress Visual Card */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-6 border-b border-subtle pb-6">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
              Longitudinal Progress Summary
            </span>
            <h1 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight mt-1">
              {targetRole} Skill Growth
            </h1>
          </div>

          <div className="text-right">
            <div className="text-xs text-secondary uppercase font-semibold">Weighted Progress</div>
            <div className="text-4xl font-extrabold text-accent-primary">{overallProgressPct}%</div>
          </div>
        </div>

        {/* Large Progress Bar Visual */}
        <div className="space-y-2">
          <div className="w-full bg-subtle h-4 rounded-full overflow-hidden p-0.5 border border-subtle">
            <div
              className="bg-gradient-to-r from-accent-primary via-accent-sky to-accent-mint h-full rounded-full transition-all duration-500"
              style={{ width: `${overallProgressPct}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted font-medium">
            <span>0% Baseline</span>
            <span>50% Target Mastery</span>
            <span>100% Job Ready</span>
          </div>
        </div>
      </div>

      {/* Skill Progress Bars */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 shadow-xs space-y-6">
        <h3 className="text-xl font-extrabold text-primary">Target Role Skill Competencies</h3>

        {skillList.length === 0 ? (
          <p className="text-xs text-secondary">
            No skill progress records found yet. Complete diagnostic check to evaluate skill competencies.
          </p>
        ) : (
          <div className="space-y-6">
            {skillList.map((skill) => {
              const masteryVal = skill.mastery ?? skill.mastery_score ?? 0;
              const masteryPct = Math.round(masteryVal * 100);
              return (
                <div key={skill.skill_id} className="space-y-2">
                  <div className="flex justify-between items-center text-sm font-semibold">
                    <span className="text-primary">{skill.skill_name}</span>
                    <span className="text-accent-primary font-bold">{masteryPct}%</span>
                  </div>
                  <div className="w-full bg-subtle h-2.5 rounded-full overflow-hidden">
                    <div
                      className="bg-accent-primary h-full rounded-full transition-all"
                      style={{ width: `${masteryPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Recent Evidence Timeline */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 shadow-xs space-y-6">
        <h3 className="text-xl font-extrabold text-primary">Recent Demonstrated Evidence</h3>

        {twinData.recent_changes && twinData.recent_changes.length > 0 ? (
          <div className="space-y-4">
            {twinData.recent_changes.map((change) => (
              <div
                key={change.id}
                className="bg-subtle/40 border border-subtle p-5 rounded-2xl flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="text-sm font-bold text-primary">{change.title}</div>
                  <div className="text-xs text-secondary">{change.description}</div>
                </div>
                <div className="text-right text-xs font-bold text-accent-primary">
                  {change.impact_delta || change.change_type}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-secondary">
            No state changes recorded yet. Complete diagnostic checks or mastery activities to stream evidence events.
          </p>
        )}
      </div>
    </div>
  );
}
