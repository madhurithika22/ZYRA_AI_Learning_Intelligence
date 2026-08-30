"use client";

import React, { useState, useEffect } from "react";
import { AuthUser, ProofOfMasteryOutcomeResponse, StartMasteryCheckResponse } from "../lib/types";
import { startMasteryCheck, submitMasteryCheck, startLearningActivity, fetchLatestActivityAttempt, fetchActiveMasteryCheck } from "../lib/api";
import { formatApiError, isValidUUID } from "../lib/formatError";
import { Button } from "./ui/Button";

interface ProofViewProps {
  user: AuthUser;
  skillName?: string;
  activityAttemptId?: string | null;
  pathNodeId?: string | null;
  onReturnOverview: () => void;
  onBackToActivity?: () => void;
}

export function ProofView({
  user,
  skillName = "Target Skill",
  activityAttemptId,
  pathNodeId,
  onReturnOverview,
  onBackToActivity,
}: ProofViewProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkSession, setCheckSession] = useState<StartMasteryCheckResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const [resolvedAttemptId, setResolvedAttemptId] = useState<string | null>(
    activityAttemptId && isValidUUID(activityAttemptId) ? activityAttemptId : null
  );
  const [attemptStatus, setAttemptStatus] = useState<"started" | "completed" | "none" | "proven">("none");
  const [attemptLoading, setAttemptLoading] = useState(true);

  const [repoUrl, setRepoUrl] = useState("");
  const [liveDemoUrl, setLiveDemoUrl] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [whatIImplemented, setWhatIImplemented] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [outcome, setOutcome] = useState<ProofOfMasteryOutcomeResponse | null>(null);

  useEffect(() => {
    async function loadAuthoritativeAttempt() {
      setAttemptLoading(true);
      setError(null);

      try {
        const latest = await fetchLatestActivityAttempt(user.learner_id, pathNodeId || undefined);
        let targetAttemptId: string | null = null;

        if (latest && isValidUUID(latest.id)) {
          targetAttemptId = latest.id;
          setResolvedAttemptId(latest.id);
          setAttemptStatus(latest.status === "completed" ? "completed" : "started");

          if (latest.submission_data && typeof latest.submission_data === "object") {
            const subData = latest.submission_data as Record<string, string>;
            if (subData.repository_url) setRepoUrl(subData.repository_url);
            if (subData.live_demo_url) setLiveDemoUrl(subData.live_demo_url);
            if (subData.project_description) setProjectDescription(subData.project_description);
            if (subData.implementation_summary) setWhatIImplemented(subData.implementation_summary);
          }
        } else if (activityAttemptId && isValidUUID(activityAttemptId)) {
          targetAttemptId = activityAttemptId;
          setResolvedAttemptId(activityAttemptId);
          setAttemptStatus("completed");
        } else {
          setResolvedAttemptId(null);
          setAttemptStatus("none");
        }

        // Restore active/recent mastery check session if present in PostgreSQL
        if (targetAttemptId && isValidUUID(targetAttemptId)) {
          const activeCheck = await fetchActiveMasteryCheck(targetAttemptId, user.learner_id);
          if (activeCheck && isValidUUID(activeCheck.check_id)) {
            setCheckSession(activeCheck);
          }
        }
      } catch (err: unknown) {
        setError(formatApiError(err));
        setAttemptStatus("none");
      } finally {
        setAttemptLoading(false);
      }
    }

    loadAuthoritativeAttempt();
  }, [user.learner_id, activityAttemptId, pathNodeId]);

  async function handleStartCheck() {
    setLoading(true);
    setError(null);
    try {
      let activeAttempt = resolvedAttemptId;
      if (!activeAttempt || !isValidUUID(activeAttempt)) {
        if (pathNodeId && isValidUUID(pathNodeId)) {
          const startRes = await startLearningActivity(pathNodeId, user.learner_id);
          activeAttempt = startRes.id;
          setResolvedAttemptId(startRes.id);
        }
      }

      if (!activeAttempt || !isValidUUID(activeAttempt)) {
        setError("This activity has not been started yet. Please complete the learning activity step first.");
        setLoading(false);
        return;
      }

      const sess = await startMasteryCheck(activeAttempt, user.learner_id);
      if (!sess || !isValidUUID(sess.check_id)) {
        setError("Your mastery check could not be initialized from the database. Please reload.");
        setLoading(false);
        return;
      }

      setCheckSession(sess);
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitAnswers(e: React.FormEvent) {
    e.preventDefault();
    if (!checkSession || !isValidUUID(checkSession.check_id)) {
      setError("Your mastery check could not be submitted. Please reload the assessment.");
      return;
    }

    if (!repoUrl.trim()) {
      setError("Repository URL is required.");
      return;
    }

    const githubRegex = /^https:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+/;
    if (!githubRegex.test(repoUrl.trim())) {
      setError("Invalid GitHub repository URL format. Please use https://github.com/username/repository.");
      return;
    }

    if (!projectDescription.trim() || !whatIImplemented.trim()) {
      setError("Project Description and What I Implemented are required.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const formattedAnswers: Array<{ question_id: string; learner_answer: string }> = [];

      for (const q of checkSession.questions) {
        if (!isValidUUID(q.question_id)) {
          setError("Assessment questions contain invalid database identifiers. Please reload.");
          setSubmitting(false);
          return;
        }

        const userAns = answers[q.question_id] || "";
        const fullAns = `Repository: ${repoUrl.trim()} | Demo: ${liveDemoUrl.trim()} | Description: ${projectDescription.trim()} | Implemented: ${whatIImplemented.trim()}${userAns ? ` | Response: ${userAns}` : ""}`;

        formattedAnswers.push({
          question_id: q.question_id,
          learner_answer: fullAns,
        });
      }

      const res = await submitMasteryCheck(
        checkSession.check_id,
        user.learner_id,
        formattedAnswers
      );
      setOutcome(res);
      setAttemptStatus("proven");
    } catch (err: unknown) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-12 space-y-8">
      {onBackToActivity && (
        <button
          type="button"
          onClick={onBackToActivity}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
        >
          <span>←</span>
          <span>Back to Activity</span>
        </button>
      )}

      <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-8">
        <div className="space-y-3">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-accent-primary-subtle text-accent-primary border border-accent-primary/20">
            PROVE WHAT YOU LEARNED
          </span>
          <h1 className="text-3xl font-extrabold text-primary tracking-tight pt-1">
            Verify Mastery: {skillName}
          </h1>
          <p className="text-sm text-secondary">
            Activity completion records practice time. Demonstrated evidence and mastery updates are recorded only after submitting an evaluation check.
          </p>
        </div>

        {error && (
          <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
            {error}
          </div>
        )}

        {/* State 1: Ready to start proof / Attempt status check */}
        {!checkSession && !outcome && (
          <div className="space-y-6 border-t border-subtle pt-6">
            {attemptLoading ? (
              <div className="py-8 text-center space-y-3">
                <div className="inline-block animate-spin h-6 w-6 text-accent-primary border-3 border-current border-t-transparent rounded-full" />
                <p className="text-xs text-secondary">Checking activity attempt status...</p>
              </div>
            ) : attemptStatus === "none" ? (
              <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl space-y-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-primary">This activity has not been started yet</h3>
                  <p className="text-xs text-secondary">
                    Please open and start your hands-on activity first to record practice progress before verifying mastery.
                  </p>
                </div>
                {onBackToActivity && (
                  <Button variant="primary" size="sm" onClick={onBackToActivity}>
                    Start Activity →
                  </Button>
                )}
              </div>
            ) : attemptStatus === "started" ? (
              <div className="bg-accent-amber-subtle border border-accent-amber/30 p-6 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-accent-secondary">
                    Activity In Progress
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-accent-amber-subtle text-accent-secondary border border-accent-amber/30">
                    STARTED
                  </span>
                </div>
                <p className="text-xs text-secondary leading-relaxed">
                  Your activity for <strong className="text-primary">{skillName}</strong> is still in progress. Complete the activity to unlock mastery evaluation check.
                </p>
                <div className="flex space-x-3 pt-2">
                  {onBackToActivity && (
                    <Button variant="secondary" size="sm" onClick={onBackToActivity}>
                      Continue Activity →
                    </Button>
                  )}
                  <Button variant="primary" size="sm" onClick={handleStartCheck} disabled={loading}>
                    {loading ? "Initializing..." : "Start Mastery Check →"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="bg-accent-mint-subtle border border-accent-mint/30 p-6 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-accent-mint">
                    Activity Complete & Ready for Proof
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-accent-mint-subtle text-accent-mint border border-accent-mint/30">
                    COMPLETED
                  </span>
                </div>
                <p className="text-xs text-secondary leading-relaxed">
                  Submit evidence for <strong className="text-primary">{skillName}</strong>. Start your evaluation check to record verified skill evidence into your Learning Twin.
                </p>
                <Button
                  variant="primary"
                  size="lg"
                  fullWidth
                  onClick={handleStartCheck}
                  disabled={loading}
                >
                  {loading ? "Initializing Assessment Check..." : "Start Mastery Check →"}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* State 2: Active Mastery Check & Question Assessment */}
        {checkSession && !outcome && (
          <form onSubmit={handleSubmitAnswers} className="space-y-6 border-t border-subtle pt-6">
            {/* 1. Assessment Questions */}
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-subtle pb-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-primary">
                  Post-Learning Verification Questions
                </h3>
                <span className="text-xs text-secondary">
                  {checkSession.questions.length} Question{checkSession.questions.length > 1 ? "s" : ""}
                </span>
              </div>

              {checkSession.questions.map((q, idx) => (
                <div key={q.question_id} className="bg-subtle/30 border border-subtle rounded-2xl p-6 space-y-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-accent-primary">Question 0{idx + 1} • {q.skill_name}</span>
                    <span className="text-secondary font-semibold">Difficulty: {q.difficulty}/5</span>
                  </div>

                  <p className="text-sm font-semibold text-primary leading-relaxed">
                    {q.prompt}
                  </p>

                  {q.options && q.options.length > 0 ? (
                    <div className="space-y-2 pt-2">
                      {q.options.map((opt, optIdx) => (
                        <label
                          key={optIdx}
                          className="flex items-center space-x-3 p-3 rounded-xl border border-subtle bg-surface hover:border-hover cursor-pointer text-xs text-primary transition-all"
                        >
                          <input
                            type="radio"
                            name={`question-${q.question_id}`}
                            value={opt}
                            checked={answers[q.question_id] === opt}
                            onChange={() => setAnswers((prev) => ({ ...prev, [q.question_id]: opt }))}
                            className="text-accent-primary focus:ring-accent-primary"
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <textarea
                      rows={3}
                      required
                      placeholder="Type your explanation / response here..."
                      value={answers[q.question_id] || ""}
                      onChange={(e) => setAnswers((prev) => ({ ...prev, [q.question_id]: e.target.value }))}
                      className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
                    />
                  )}
                </div>
              ))}
            </div>

            {/* 2. Repository Deliverables */}
            <div className="space-y-4 pt-4 border-t border-subtle">
              <h3 className="text-sm font-bold uppercase tracking-wider text-primary">
                Deliverables & Evidence Context
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-primary mb-1">
                    Repository URL *
                  </label>
                  <input
                    type="url"
                    required
                    placeholder="https://github.com/username/repository"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-primary mb-1">
                    LIVE DEMO URL (OPTIONAL)
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
                    PROJECT DESCRIPTION *
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Describe the architecture and scope of your implementation..."
                    value={projectDescription}
                    onChange={(e) => setProjectDescription(e.target.value)}
                    className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-primary mb-1">
                    WHAT I IMPLEMENTED *
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Detail the specific containers, Dockerfile configurations, health endpoints, and test commands..."
                    value={whatIImplemented}
                    onChange={(e) => setWhatIImplemented(e.target.value)}
                    className="w-full bg-surface border border-subtle rounded-xl p-3 text-xs text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              fullWidth
              disabled={submitting}
              type="submit"
            >
              {submitting ? "Evaluating Proof Evidence..." : "Submit Mastery Verification →"}
            </Button>
          </form>
        )}

        {/* State 3: Evaluated Outcome */}
        {outcome && (
          <div className="space-y-8 pt-4 border-t border-subtle">
            <div className="flex items-center space-x-3 text-accent-mint font-bold text-lg">
              <span>✓ Verified Mastery Evidence Recorded</span>
            </div>

            <p className="text-xs text-secondary leading-relaxed bg-subtle/40 border border-subtle p-4 rounded-2xl">
              {outcome.overall_explanation}
            </p>

            {outcome.skill_outcomes.map((so) => (
              <div key={so.skill_id} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-subtle/40 border border-subtle p-6 rounded-2xl text-center space-y-1">
                    <div className="text-xs font-semibold text-secondary uppercase">BEFORE</div>
                    <div className="text-3xl font-extrabold text-muted">
                      {Math.round(so.before_mastery * 100)}%
                    </div>
                  </div>

                  <div className="bg-accent-primary-subtle border border-accent-primary/30 p-6 rounded-2xl text-center space-y-1">
                    <div className="text-xs font-bold text-accent-primary uppercase">MASTERY DELTA</div>
                    <div className="text-3xl font-extrabold text-accent-primary">
                      {so.mastery_delta >= 0 ? `+${Math.round(so.mastery_delta * 100)}` : Math.round(so.mastery_delta * 100)} pts
                    </div>
                  </div>

                  <div className="bg-accent-mint-subtle border border-accent-mint/30 p-6 rounded-2xl text-center space-y-1">
                    <div className="text-xs font-bold text-accent-mint uppercase">AFTER</div>
                    <div className="text-3xl font-extrabold text-accent-mint">
                      {Math.round(so.after_mastery * 100)}%
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div className="bg-subtle/30 p-4 rounded-xl border border-subtle">
                    <div className="text-[11px] font-semibold text-secondary uppercase">CONFIDENCE DELTA</div>
                    <div className="text-sm font-bold text-primary mt-1">
                      {Math.round(so.before_confidence * 100)}% → {Math.round(so.after_confidence * 100)}%
                    </div>
                  </div>
                  <div className="bg-subtle/30 p-4 rounded-xl border border-subtle">
                    <div className="text-[11px] font-semibold text-secondary uppercase">EVIDENCE QUALITY</div>
                    <div className="text-sm font-bold text-primary mt-1">
                      {Math.round(so.evidence_quality * 100)}%
                    </div>
                  </div>
                  <div className="bg-subtle/30 p-4 rounded-xl border border-subtle">
                    <div className="text-[11px] font-semibold text-secondary uppercase">PROOF STRENGTH</div>
                    <div className="text-sm font-bold text-primary mt-1">
                      {Math.round(so.proof_strength * 100)}%
                    </div>
                  </div>
                  <div className="bg-subtle/30 p-4 rounded-xl border border-subtle">
                    <div className="text-[11px] font-semibold text-secondary uppercase">CLASSIFICATION</div>
                    <div className="text-sm font-bold text-accent-mint mt-1 capitalize">
                      {so.classification.replace("_", " ")}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            <Button variant="primary" size="lg" fullWidth onClick={onReturnOverview}>
              Return to Learning Twin Overview →
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
