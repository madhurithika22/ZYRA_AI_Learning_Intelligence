"use client";

import React, { useState, useEffect } from "react";
import { AuthUser } from "../lib/types";
import { startLearningActivity, completeLearningActivity, saveActivityDraft, fetchActiveActivityAttempt } from "../lib/api";
import { formatApiError, isValidUUID } from "../lib/formatError";
import { Button } from "./ui/Button";


export interface ActiveActivityAttempt {
  id: string;
  learner_id: string;
  learning_path_node_id: string;
  status: "started" | "draft" | "submitted" | "completed";
  attempt_number: number;
  created_at?: string;
  updated_at?: string;
  submitted_at?: string | null;
  repository_url: string;
  live_demo_url: string;
  project_description: string;
  implementation_summary: string;
}

interface ActivityViewProps {
  user?: AuthUser;
  pathNodeId?: string;
  skillName?: string;
  activityTitle?: string;
  estimatedMinutes?: number;
  rationale?: string;
  resourceUrl?: string | null;
  onCompleteActivity?: (attemptId: string) => void;
  onProveMastery: (attemptId?: string) => void;
  onBackToPath?: () => void;
}

export function ActivityView({
  user,
  pathNodeId,
  skillName = "Docker",
  activityTitle = "Build a containerized ML inference service",
  estimatedMinutes = 30,
  rationale = "Targeted exercise designed to address your active bottleneck.",
  resourceUrl,
  onCompleteActivity,
  onProveMastery,
  onBackToPath,
}: ActivityViewProps) {
  const [activeActivityAttempt, setActiveActivityAttempt] = useState<ActiveActivityAttempt | null>(null);
  const [effectiveNodeId, setEffectiveNodeId] = useState<string | null>(pathNodeId || null);
  const [status, setStatus] = useState<"not_started" | "started" | "draft" | "submitted" | "completed">("not_started");

  const [loading, setLoading] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftSavedMessage, setDraftSavedMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Independent Form Input Fields
  const [githubUrl, setGithubUrl] = useState("");
  const [liveDemoUrl, setLiveDemoUrl] = useState("");
  const [builtDescription, setBuiltDescription] = useState("");
  const [whatIImplemented, setWhatIImplemented] = useState("");

  useEffect(() => {
    let active = true;
    async function loadAttempt() {
      if (!user) return;
      try {
        const activeRes = await fetchActiveActivityAttempt();
        if (!active) return;

        if (activeRes.attempt) {
          const att = activeRes.attempt;
          const subData = (att.submission_data && typeof att.submission_data === "object")
            ? (att.submission_data as Record<string, string>)
            : {};

          const canonicalAttempt: ActiveActivityAttempt = {
            id: att.id,
            learner_id: att.learner_id,
            learning_path_node_id: att.learning_path_node_id,
            status: att.status === "completed" || att.status === "submitted" ? "completed" : att.status === "draft" ? "draft" : "started",
            attempt_number: att.attempt_number,
            created_at: att.started_at,
            submitted_at: att.completed_at,
            repository_url: subData.repository_url || "",
            live_demo_url: subData.live_demo_url || "",
            project_description: subData.project_description || "",
            implementation_summary: subData.implementation_summary || subData.what_i_implemented || "",
          };

          setActiveActivityAttempt(canonicalAttempt);
          setEffectiveNodeId(att.learning_path_node_id);
          setStatus(canonicalAttempt.status);

          // Populate form fields strictly from persisted values — NEVER cross-contaminate fields
          setGithubUrl(canonicalAttempt.repository_url);
          setLiveDemoUrl(canonicalAttempt.live_demo_url);
          setBuiltDescription(canonicalAttempt.project_description);
          setWhatIImplemented(canonicalAttempt.implementation_summary);
        } else if (activeRes.node_id) {
          setEffectiveNodeId(activeRes.node_id);
          setStatus("not_started");
        } else if (pathNodeId) {
          setEffectiveNodeId(pathNodeId);
          setStatus("not_started");
        }
      } catch (err: unknown) {
        if (active && pathNodeId) setEffectiveNodeId(pathNodeId);
      }
    }
    loadAttempt();
    return () => {
      active = false;
    };
  }, [user, pathNodeId]);

  async function handleStart() {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      // Fetch authoritative node ID directly from backend active attempt endpoint
      let targetNodeId: string | null = null;
      try {
        const activeRes = await fetchActiveActivityAttempt();
        if (activeRes.node_id && isValidUUID(activeRes.node_id)) {
          targetNodeId = activeRes.node_id;
          setEffectiveNodeId(activeRes.node_id);
        }
      } catch (err: unknown) {
        // Fallback to state if active resolution call encounters error
      }

      if (!targetNodeId) {
        targetNodeId = effectiveNodeId || pathNodeId || null;
      }

      if (!targetNodeId || !isValidUUID(targetNodeId)) {
        setError("No active learning path node found. Please generate or select a learning path first.");
        setLoading(false);
        return;
      }

      console.debug("[ACTIVITY_START] Starting activity for node:", targetNodeId);
      const res = await startLearningActivity(targetNodeId, user.learner_id);
      console.debug("[ACTIVITY_START] Activity started successfully. Attempt ID:", res.id);

      const newAttempt: ActiveActivityAttempt = {
        id: res.id,
        learner_id: res.learner_id,
        learning_path_node_id: res.learning_path_node_id,
        status: "started",
        attempt_number: res.attempt_number,
        created_at: res.started_at,
        repository_url: "",
        live_demo_url: "",
        project_description: "",
        implementation_summary: "",
      };
      setActiveActivityAttempt(newAttempt);
      setEffectiveNodeId(res.learning_path_node_id);
      setStatus("started");
    } catch (err: unknown) {
      console.error("[ACTIVITY_START_ERROR]", err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }


  async function handleSaveDraft() {
    if (!user) return;
    setSavingDraft(true);
    setError(null);
    setDraftSavedMessage(null);

    try {
      let attemptId = activeActivityAttempt?.id;
      const targetNodeId = effectiveNodeId || pathNodeId;

      if (!attemptId || !isValidUUID(attemptId)) {
        if (targetNodeId && isValidUUID(targetNodeId)) {
          const startRes = await startLearningActivity(targetNodeId, user.learner_id);
          attemptId = startRes.id;
          setEffectiveNodeId(startRes.learning_path_node_id);
        }
      }

      if (!attemptId || !isValidUUID(attemptId)) {
        setError("Activity attempt could not be resolved from backend. Please refresh.");
        setSavingDraft(false);
        return;
      }

      // Fields are mapped strictly and independently — NEVER fall back to repository_url
      const subData = {
        repository_url: githubUrl.trim(),
        live_demo_url: liveDemoUrl.trim(),
        project_description: builtDescription.trim(),
        implementation_summary: whatIImplemented.trim(),
        what_i_implemented: whatIImplemented.trim(),
      };

      const updated = await saveActivityDraft(attemptId, user.learner_id, subData);
      setActiveActivityAttempt({
        id: updated.id,
        learner_id: updated.learner_id,
        learning_path_node_id: updated.learning_path_node_id,
        status: "draft",
        attempt_number: updated.attempt_number,
        created_at: updated.started_at,
        repository_url: githubUrl.trim(),
        live_demo_url: liveDemoUrl.trim(),
        project_description: builtDescription.trim(),
        implementation_summary: whatIImplemented.trim(),
      });
      setStatus("draft");
      setDraftSavedMessage("Draft saved to database.");
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setSavingDraft(false);
    }
  }

  async function handleSubmitActivity() {
    if (!user) return;
    if (!githubUrl.trim()) {
      setError("Repository URL is required.");
      return;
    }
    const githubRegex = /^https:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+/;
    if (!githubRegex.test(githubUrl.trim())) {
      setError("Invalid GitHub repository URL format. Use format: https://github.com/username/repository");
      return;
    }
    if (!builtDescription.trim()) {
      setError("Project Description ('What Did You Build?') is required.");
      return;
    }
    if (!whatIImplemented.trim()) {
      setError("Implementation Summary ('What I Implemented') is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setDraftSavedMessage(null);

    try {
      let attemptId = activeActivityAttempt?.id;
      const targetNodeId = effectiveNodeId || pathNodeId;

      if (!attemptId || !isValidUUID(attemptId)) {
        if (targetNodeId && isValidUUID(targetNodeId)) {
          const startRes = await startLearningActivity(targetNodeId, user.learner_id);
          attemptId = startRes.id;
          setEffectiveNodeId(startRes.learning_path_node_id);
        }
      }

      if (!attemptId || !isValidUUID(attemptId)) {
        setError("Activity attempt could not be resolved from backend. Please refresh.");
        setLoading(false);
        return;
      }

      // Fields are mapped strictly and independently — NEVER fall back to repository_url
      const subData = {
        repository_url: githubUrl.trim(),
        live_demo_url: liveDemoUrl.trim(),
        project_description: builtDescription.trim(),
        implementation_summary: whatIImplemented.trim(),
        what_i_implemented: whatIImplemented.trim(),
        submitted_at: new Date().toISOString(),
      };

      const completed = await completeLearningActivity(attemptId, user.learner_id, subData);
      setActiveActivityAttempt({
        id: completed.id,
        learner_id: completed.learner_id,
        learning_path_node_id: completed.learning_path_node_id,
        status: "completed",
        attempt_number: completed.attempt_number,
        created_at: completed.started_at,
        submitted_at: completed.completed_at,
        repository_url: githubUrl.trim(),
        live_demo_url: liveDemoUrl.trim(),
        project_description: builtDescription.trim(),
        implementation_summary: whatIImplemented.trim(),
      });
      setStatus("completed");

      if (onCompleteActivity && attemptId) {
        onCompleteActivity(attemptId);
      }
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-12 space-y-8">
      {onBackToPath && (
        <button
          type="button"
          onClick={onBackToPath}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
        >
          <span>←</span>
          <span>Back to Learning Path</span>
        </button>
      )}

      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        {/* Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-accent-primary-subtle text-accent-primary border border-accent-primary/20">
              HANDS-ON PROJECT
            </span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${
                status === "completed"
                  ? "bg-accent-mint-subtle text-accent-mint border-accent-mint/30"
                  : status === "started" || status === "draft"
                  ? "bg-accent-primary-subtle text-accent-primary border-accent-primary/30"
                  : "bg-subtle text-secondary border-subtle"
              }`}
            >
              {status === "started" ? "IN PROGRESS" : status.replace("_", " ")}
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight">
            {activityTitle}
          </h1>

          <div className="flex items-center space-x-4 text-xs font-semibold text-secondary pt-1">
            <span>Target Skill: <strong className="text-primary">{skillName}</strong></span>
            <span>•</span>
            <span>Est. Time: {estimatedMinutes} Mins</span>
          </div>
        </div>

        {error && (
          <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
            {error}
          </div>
        )}

        {/* Why this matters */}
        <div className="space-y-2 border-t border-subtle pt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
            Why this matters
          </h3>
          <p className="text-sm text-secondary leading-relaxed">{rationale}</p>
        </div>

        {/* YOUR TASK */}
        <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-primary">
            YOUR TASK
          </h3>
          <ol className="list-decimal list-inside text-xs text-secondary space-y-2 leading-relaxed font-medium">
            <li>Create a Dockerfile</li>
            <li>Containerize the inference API</li>
            <li>Expose the required port</li>
            <li>Add a health endpoint</li>
            <li>Document how to run the container</li>
          </ol>
        </div>

        {/* DELIVERABLES & INPUTS */}
        <div className="space-y-4 border-t border-subtle pt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
            DELIVERABLE
          </h3>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-primary mb-1">
                GitHub Repository
              </label>
              <input
                type="url"
                placeholder="https://github.com/username/project"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-primary mb-1">
                OPTIONAL LIVE DEMO
              </label>
              <input
                type="url"
                placeholder="https://demo-service.com"
                value={liveDemoUrl}
                onChange={(e) => setLiveDemoUrl(e.target.value)}
                className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-primary mb-1">
                WHAT DID YOU BUILD?
              </label>
              <textarea
                rows={3}
                placeholder="Describe your project, design decisions, and how to execute your containerized service..."
                value={builtDescription}
                onChange={(e) => setBuiltDescription(e.target.value)}
                className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-primary mb-1">
                WHAT I IMPLEMENTED
              </label>
              <textarea
                rows={3}
                placeholder="Summarize key features, components, endpoints, or scripts implemented..."
                value={whatIImplemented}
                onChange={(e) => setWhatIImplemented(e.target.value)}
                className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
              />
            </div>
          </div>

        </div>

        {/* LEARNING RESOURCES */}
        <div className="space-y-3 border-t border-subtle pt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
            LEARNING RESOURCES
          </h3>
          <div className="flex flex-wrap gap-3">
            {resourceUrl && resourceUrl.startsWith("http") ? (
              <button
                type="button"
                onClick={() => window.open(resourceUrl, "_blank", "noopener,noreferrer")}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-accent-rose-subtle hover:opacity-90 text-accent-rose border border-accent-rose/30 transition-all flex items-center space-x-1.5"
              >
                <span>YouTube Video →</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => window.open("https://www.youtube.com/results?search_query=docker+machine+learning", "_blank", "noopener,noreferrer")}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-accent-rose-subtle hover:opacity-90 text-accent-rose border border-accent-rose/30 transition-all flex items-center space-x-1.5"
              >
                <span>YouTube Playlist →</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => window.open("https://docs.docker.com/get-started/", "_blank", "noopener,noreferrer")}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-subtle hover:bg-subtle/80 text-primary border border-subtle transition-all flex items-center space-x-1.5"
            >
              <span>Documentation →</span>
            </button>
          </div>
        </div>

        {draftSavedMessage && (
          <div className="bg-accent-mint-subtle border border-accent-mint/30 rounded-2xl p-4 text-xs font-semibold text-accent-mint">
            ✓ {draftSavedMessage}
          </div>
        )}

        {/* ACTION BUTTON / CTA */}
        <div className="border-t border-subtle pt-6">
          {status === "not_started" && (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleStart}
              disabled={loading}
            >
              {loading ? "Starting Activity..." : "Start Activity →"}
            </Button>
          )}

          {(status === "started" || status === "draft") && (
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                variant="secondary"
                size="lg"
                fullWidth
                onClick={handleSaveDraft}
                disabled={savingDraft || loading}
              >
                {savingDraft ? "Saving Draft..." : "Save Draft"}
              </Button>

              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleSubmitActivity}
                disabled={loading || savingDraft}
              >
                {loading ? "Submitting..." : "Submit Activity for Review →"}
              </Button>
            </div>
          )}

          {status === "completed" && (
            <div className="space-y-4">
              <div className="bg-accent-mint-subtle border border-accent-mint/30 rounded-2xl p-4 text-xs font-semibold text-accent-mint">
                ✓ Submission Received. Your mastery estimate remains unchanged until evidence is evaluated in the proof stage.
              </div>

              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={() => onProveMastery(activeActivityAttempt?.id || undefined)}
              >
                Prove What You Learned →
              </Button>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
