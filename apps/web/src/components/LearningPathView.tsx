"use client";

import React, { useState } from "react";
import { PathComparisonResponse } from "../lib/types";
import { Button } from "./ui/Button";

interface LearningPathViewProps {
  pathData: PathComparisonResponse | null;
  loading: boolean;
  onGenerate: () => void;
  onSelectNode?: (nodeId: string) => void;
  onBackToOverview?: () => void;
}

export function LearningPathView({
  pathData,
  loading,
  onGenerate,
  onSelectNode,
  onBackToOverview,
}: LearningPathViewProps) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>("BALANCED");

  if (loading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="inline-block animate-spin h-8 w-8 text-accent-primary border-4 border-current border-t-transparent rounded-full" />
        <p className="text-secondary text-sm">Optimizing learning path strategy options...</p>
      </div>
    );
  }

  if (!pathData || !pathData.options) {
    return (
      <div className="bg-surface border border-subtle rounded-3xl p-12 text-center max-w-2xl mx-auto space-y-6 shadow-xs">
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Adaptive Path Engine
          </span>
          <h3 className="text-3xl font-extrabold text-primary">YOUR ADAPTIVE PATH</h3>
          <p className="text-secondary text-sm max-w-md mx-auto leading-relaxed">
            Your learner state is ready. Choose how you want to learn to generate candidate learning path options.
          </p>
        </div>
        <div className="flex justify-center pt-2">
          <Button variant="primary" size="lg" onClick={onGenerate}>
            Generate My Learning Path →
          </Button>
        </div>
      </div>
    );
  }

  const activeOption = pathData.options[selectedStrategy] || Object.values(pathData.options)[0];

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

      {/* Strategy Tabs Header */}
      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-subtle pb-6">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
              Learning Path Optimizer
            </span>
            <h1 className="text-3xl font-extrabold text-primary tracking-tight mt-1">
              Strategy Candidates
            </h1>
          </div>

          <div className="flex items-center space-x-2 bg-subtle p-1.5 rounded-2xl">
            {Object.keys(pathData.options).map((stratKey) => (
              <button
                key={stratKey}
                onClick={() => setSelectedStrategy(stratKey)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  selectedStrategy === stratKey
                    ? "bg-surface text-primary shadow-xs"
                    : "text-secondary hover:text-primary"
                }`}
              >
                {stratKey}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Strategy Detail Card */}
        {activeOption && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-2xl font-extrabold text-primary">
                {activeOption.strategy_name || activeOption.name || selectedStrategy}
              </h2>
              <div className="flex items-center space-x-4 text-xs font-semibold">
                <span className="px-3 py-1 rounded-full bg-subtle text-accent-primary">
                  {activeOption.estimated_days ?? (activeOption.estimated_weeks ? Math.round(activeOption.estimated_weeks * 7) : 14)} Days
                </span>
                <span className="px-3 py-1 rounded-full bg-subtle text-accent-mint">
                  {activeOption.total_minutes ?? activeOption.estimated_minutes ?? 120} Total Minutes
                </span>
                <span className="px-3 py-1 rounded-full bg-subtle text-accent-sky">
                  {Math.round((activeOption.target_skill_coverage ?? activeOption.target_role_coverage ?? 1.0) * 100)}% Role Coverage
                </span>
              </div>
            </div>
            <p className="text-sm text-secondary leading-relaxed">
              {activeOption.description || activeOption.explanation}
            </p>
          </div>
        )}
      </div>

      {/* Visual Timeline Nodes */}
      {activeOption && activeOption.nodes && (
        <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-10 shadow-xs space-y-8">
          <h3 className="text-xl font-extrabold text-primary">Sequential Activity Timeline</h3>

          <div className="relative pl-6 space-y-8 border-l-2 border-subtle">
            {activeOption.nodes.map((node, i) => {
              const nodeUrl = node.resource_url;
              return (
                <div
                  key={node.node_id || node.id || node.resource_id || `node-${i}`}
                  className="relative group space-y-4"
                >
                  {/* Node dot */}
                  <div
                    className={`absolute -left-[31px] top-1.5 h-4 w-4 rounded-full border-2 bg-surface transition-transform group-hover:scale-125 ${
                      node.is_bottleneck
                        ? "border-accent-secondary bg-accent-secondary"
                        : "border-accent-primary bg-accent-primary"
                    }`}
                  />

                  <div className="bg-subtle/40 border border-subtle rounded-2xl p-6 hover:border-hover transition-all space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-3">
                        <span className="text-xs font-bold text-muted">
                          0{i + 1}
                        </span>
                        <div>
                          <span className="text-[10px] uppercase font-bold text-accent-primary">
                            Target Skill: {node.skill_name || "Competency Step"}
                          </span>
                          <h4 className="text-lg font-bold text-primary">
                            {node.resource_title || node.skill_name}
                          </h4>
                        </div>
                      </div>
                      {node.is_bottleneck && (
                        <span className="px-3 py-1 rounded-full bg-accent-amber-subtle text-accent-secondary text-xs font-bold border border-accent-amber/30">
                          Bottleneck Node
                        </span>
                      )}
                    </div>

                    {node.rationale && (
                      <p className="text-xs text-secondary leading-relaxed border-t border-subtle/60 pt-3">
                        <strong className="text-primary font-semibold">Why this step:</strong> {node.rationale}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-subtle/60">
                      <div className="flex items-center space-x-3 text-xs text-secondary">
                        <span>Type: {node.activity_type || node.resource_type || "Exercise"}</span>
                        <span>•</span>
                        <span>Est. Time: {node.estimated_minutes} mins</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {nodeUrl && nodeUrl.startsWith("http") && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(nodeUrl, "_blank", "noopener,noreferrer");
                            }}
                            className="px-4 py-2 rounded-xl text-xs font-bold bg-accent-rose-subtle hover:opacity-90 text-accent-rose border border-accent-rose/30 transition-all flex items-center space-x-1.5"
                          >
                            <span>Watch on YouTube</span>
                            <span>↗</span>
                          </button>
                        )}

                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => onSelectNode && onSelectNode(node.node_id || node.id || "")}
                        >
                          Start Activity →
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
