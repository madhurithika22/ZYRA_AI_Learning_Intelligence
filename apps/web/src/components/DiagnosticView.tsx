"use client";

import React, { useState, useEffect } from "react";
import {
  getNextQuestion,
  submitDiagnosticAnswer,
  startDiagnosticSession,
  fetchLatestDiagnosticSession,
  fetchLearnerSkillState,
  submitSelfAssessment,
  fetchDiagnosticHistory,
} from "../lib/api";
import { AuthUser, DiagnosticQuestion, DiagnosticHistoryItem } from "../lib/types";
import { formatApiError } from "../lib/formatError";
import { Button } from "./ui/Button";

interface DiagnosticViewProps {
  user: AuthUser;
  goalId: string | null;
  onDiagnosticComplete: () => void;
  onNavigateToTab?: (tab: string) => void;
  onBackToGoal?: () => void;
}

interface SkillStateItem {
  skill_id: string;
  skill_name: string;
  required_level: number;
  role_importance: number;
  mastery_score: number;
  confidence: number;
  evidence_count: number;
}

type DiagnosticUiStage =
  | "NOT_STARTED"
  | "SELF_ASSESSMENT"
  | "READY"
  | "INTERRUPTED"
  | "IN_PROGRESS"
  | "EVALUATING"
  | "NEXT_QUESTION"
  | "COMPLETE";

export function DiagnosticView({
  user,
  goalId,
  onDiagnosticComplete,
  onNavigateToTab,
  onBackToGoal,
}: DiagnosticViewProps) {
  const [uiStage, setUiStage] = useState<DiagnosticUiStage>("NOT_STARTED");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(goalId));
  const [question, setQuestion] = useState<DiagnosticQuestion | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState<{
    score: number;
    feedback: string;
    new_mastery: number;
  } | null>(null);

  const [skillStateList, setSkillStateList] = useState<SkillStateItem[]>([]);
  const [targetRoleName, setTargetRoleName] = useState<string>("Target Role");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selfAssessmentPriors, setSelfAssessmentPriors] = useState<Record<string, string>>({});
  const [diagnosticHistory, setDiagnosticHistory] = useState<DiagnosticHistoryItem[]>([]);

  // Per-skill attempt counters
  const [skillAttemptStats, setSkillAttemptStats] = useState<
    Record<string, { attempted: number; correct: number }>
  >({});

  useEffect(() => {
    if (goalId) {
      checkExistingSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [goalId]);

  async function checkExistingSession() {
    if (!goalId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const latest = await fetchLatestDiagnosticSession(user.learner_id, goalId);
      await loadSkillState();
      await loadHistory();

      if (latest) {
        setSessionId(latest.session_id);
        if (latest.status === "completed") {
          setUiStage("COMPLETE");
        } else if (latest.status === "in_progress") {
          if (latest.question_count > 0) {
            setUiStage("INTERRUPTED");
          } else {
            setUiStage("SELF_ASSESSMENT");
          }
        }
      } else {
        setUiStage("NOT_STARTED");
      }
    } catch (err: unknown) {
      setErrorMsg(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadSkillState() {
    if (!goalId) return;
    try {
      const res = await fetchLearnerSkillState(user.learner_id, goalId);
      if (res) {
        setTargetRoleName(res.target_role || "Target Role");
        setSkillStateList(res.skills || []);
      }
    } catch {
      // Fallback
    }
  }

  async function loadHistory() {
    if (!goalId) return;
    try {
      const res = await fetchDiagnosticHistory(user.learner_id, goalId);
      if (res && res.history) {
        setDiagnosticHistory(res.history);
      }
    } catch {
      // Fallback
    }
  }

  async function handleStartNewDiagnostic(forceNew: boolean = false) {
    if (!goalId) {
      setErrorMsg("Please define and save your learning goal first.");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    setQuestion(null);
    setEvaluation(null);
    setSelectedOption(null);
    setSkillAttemptStats({});
    try {
      const res = await startDiagnosticSession(user.learner_id, goalId, forceNew);
      setSessionId(res.session_id);
      setUiStage("SELF_ASSESSMENT");
    } catch (err: unknown) {
      setErrorMsg(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSelfAssessmentSubmit() {
    if (!sessionId) return;
    setLoading(true);
    try {
      await submitSelfAssessment(sessionId, selfAssessmentPriors);
      setUiStage("READY");
      await loadNextQuestion(sessionId);
    } catch (err: unknown) {
      setErrorMsg(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadNextQuestion(sessId: string) {
    setEvaluation(null);
    setSelectedOption(null);
    setErrorMsg(null);
    try {
      const q = await getNextQuestion(sessId);
      if (q) {
        setQuestion(q);
        setUiStage("IN_PROGRESS");
      } else {
        setUiStage("COMPLETE");
        await loadSkillState();
        await loadHistory();
      }
    } catch (err: unknown) {
      setErrorMsg(formatApiError(err));
    }
  }

  async function handleSubmitAnswer() {
    if (!sessionId || !question || !selectedOption) return;
    setSubmitting(true);
    setUiStage("EVALUATING");
    try {
      const evalResult = await submitDiagnosticAnswer(
        sessionId,
        question.question_id,
        selectedOption
      );
      if (evalResult) {
        setEvaluation({
          score: evalResult.demonstrated_score,
          feedback: evalResult.evaluation_feedback,
          new_mastery: evalResult.updated_mastery,
        });

        // Track stats per skill
        setSkillAttemptStats((prev) => {
          const current = prev[question.skill_name] || { attempted: 0, correct: 0 };
          return {
            ...prev,
            [question.skill_name]: {
              attempted: current.attempted + 1,
              correct: current.correct + (evalResult.demonstrated_score >= 0.7 ? 1 : 0),
            },
          };
        });

        if (evalResult.is_session_completed) {
          setTimeout(async () => {
            setUiStage("COMPLETE");
            await loadSkillState();
            await loadHistory();
          }, 1500);
        } else {
          setUiStage("NEXT_QUESTION");
        }
      }
    } catch (err: unknown) {
      setErrorMsg(formatApiError(err));
      setUiStage("IN_PROGRESS");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-24 text-center space-y-4">
        <div className="inline-block animate-spin h-8 w-8 text-accent-primary border-4 border-current border-t-transparent rounded-full" />
        <p className="text-secondary text-sm font-medium">Checking diagnostic state...</p>
      </div>
    );
  }

  const assessedSkillsCount = skillStateList.filter((s) => s.evidence_count > 0).length;
  const totalSkillsCount = skillStateList.length || 6;

  /* STAGE: INTERRUPTED (Session Interruption Recovery) */
  if (uiStage === "INTERRUPTED" && sessionId) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-6 animate-in fade-in duration-300">
        <div className="bg-surface border border-subtle rounded-3xl p-8 sm:p-12 space-y-6 shadow-xs">
          <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-accent-amber-subtle text-accent-secondary border border-accent-amber/30">
            RESUME DIAGNOSTIC
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-primary tracking-tight">
            WELCOME BACK
          </h2>
          <p className="text-secondary text-sm max-w-md mx-auto leading-relaxed">
            You were in the middle of your adaptive diagnostic check for <strong className="text-primary">{targetRoleName}</strong>.
          </p>
          <div className="flex justify-center gap-4 pt-2">
            <Button
              variant="primary"
              size="lg"
              onClick={() => {
                setUiStage("READY");
                loadNextQuestion(sessionId);
              }}
            >
              Continue Diagnostic →
            </Button>
            <Button
              variant="ghost"
              size="lg"
              onClick={() => setUiStage("NOT_STARTED")}
            >
              Exit & Resume Later
            </Button>
          </div>
        </div>
      </div>
    );
  }

  /* STAGE: SELF_ASSESSMENT (Phase 6 Pre-Assessment Ratings) */
  if (uiStage === "SELF_ASSESSMENT") {
    const ratingsOptions = ["New to it", "Familiar", "Comfortable", "Advanced"];
    return (
      <div className="max-w-3xl mx-auto py-8 sm:py-12 space-y-8 animate-in fade-in duration-300">
        <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="space-y-2 border-b border-subtle pb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
              Phase 1 of 2 • Baseline Prior
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-primary tracking-tight">
              BEFORE WE START
            </h2>
            <p className="text-xs text-secondary">
              How familiar are you with each area required for <strong className="text-primary">{targetRoleName}</strong>?
            </p>
          </div>

          <div className="space-y-5">
            {skillStateList.map((skill) => (
              <div key={skill.skill_id} className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-2">
                <span className="text-sm font-extrabold text-primary">{skill.skill_name}</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  {ratingsOptions.map((opt) => {
                    const isSelected = selfAssessmentPriors[skill.skill_name] === opt;
                    return (
                      <button
                        key={opt}
                        type="button"
                        onClick={() =>
                          setSelfAssessmentPriors((prev) => ({
                            ...prev,
                            [skill.skill_name]: opt,
                          }))
                        }
                        className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
                          isSelected
                            ? "border-accent-primary bg-accent-primary text-white shadow-xs"
                            : "border-subtle hover:border-hover bg-surface text-secondary"
                        }`}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-4 border-t border-subtle">
            <Button
              variant="primary"
              size="md"
              onClick={handleSelfAssessmentSubmit}
            >
              Start Adaptive Diagnostic Questions →
            </Button>
          </div>
        </div>
      </div>
    );
  }

  /* STAGE: COMPLETE (Phase 10, 11, 12, 14, 23 Summary View) */
  if (uiStage === "COMPLETE") {
    const strongest = [...skillStateList].sort((a, b) => b.mastery_score - a.mastery_score)[0];
    const opportunity = [...skillStateList].sort((a, b) => a.mastery_score - b.mastery_score)[0];
    const lowConfidence = skillStateList.filter((s) => s.confidence < 0.7);

    return (
      <div className="max-w-4xl mx-auto py-8 sm:py-12 space-y-8 animate-in fade-in duration-300">
        {onBackToGoal && (
          <button
            type="button"
            onClick={onBackToGoal}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-subtle hover:bg-subtle/80 text-secondary hover:text-primary transition-all flex items-center space-x-2"
          >
            <span>←</span>
            <span>Back to My Goal</span>
          </button>
        )}

        <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-10 shadow-xs space-y-8">
          {/* Phase 23 Sophisticated Celebration Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-subtle pb-6">
            <div className="space-y-1">
              <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-accent-mint-subtle text-accent-mint border border-accent-mint/30">
                YOUR BASELINE IS READY
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-primary pt-2 tracking-tight">
                Confirmed Skill State Analysis
              </h2>
              <p className="text-xs text-secondary">
                Measured baseline for <strong className="text-primary">{targetRoleName}</strong> based on adaptive evidence.
              </p>
            </div>

            <Button variant="ghost" size="sm" onClick={() => handleStartNewDiagnostic(true)}>
              Re-diagnose ↻
            </Button>
          </div>

          {/* Phase 10 Key Highlights: Strongest & Opportunity */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-accent-mint-subtle/40 border border-accent-mint/30 space-y-1">
              <span className="text-[11px] font-bold uppercase text-accent-mint">YOUR STRONGEST SKILL</span>
              <p className="font-extrabold text-primary text-sm">{strongest ? strongest.skill_name : "N/A"}</p>
              <p className="text-xs font-semibold text-accent-mint">{strongest ? `${Math.round(strongest.mastery_score * 100)}% mastery` : ""}</p>
            </div>

            <div className="p-4 rounded-2xl bg-accent-rose-subtle/40 border border-accent-rose/30 space-y-1">
              <span className="text-[11px] font-bold uppercase text-accent-rose">YOUR BIGGEST OPPORTUNITY</span>
              <p className="font-extrabold text-primary text-sm">{opportunity ? opportunity.skill_name : "N/A"}</p>
              <p className="text-xs font-semibold text-accent-rose">{opportunity ? `${Math.round(opportunity.mastery_score * 100)}% mastery` : ""}</p>
            </div>

            <div className="p-4 rounded-2xl bg-accent-amber-subtle/40 border border-accent-amber/30 space-y-1">
              <span className="text-[11px] font-bold uppercase text-accent-secondary">LOW-CONFIDENCE AREAS</span>
              <p className="font-extrabold text-primary text-sm truncate">
                {lowConfidence.length > 0 ? lowConfidence.map((s) => s.skill_name).join(", ") : "None"}
              </p>
              <p className="text-xs text-muted">{lowConfidence.length} skills need calibration</p>
            </div>
          </div>

          {/* Phase 12 Per-Skill Cards */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-primary">Skill Calibrations</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {skillStateList.map((skill) => {
                const isAssessed = skill.evidence_count > 0 || skill.confidence > 0;
                const stats = skillAttemptStats[skill.skill_name] || { attempted: skill.evidence_count, correct: 0 };
                const priorRating = selfAssessmentPriors[skill.skill_name];

                let badge = "Not Assessed";
                let badgeClass = "bg-subtle text-secondary";
                if (isAssessed && skill.mastery_score >= 0.7) {
                  badge = "Strong";
                  badgeClass = "bg-accent-mint-subtle text-accent-mint border-accent-mint/30";
                } else if (isAssessed && skill.mastery_score >= 0.4) {
                  badge = "Developing";
                  badgeClass = "bg-accent-primary-subtle text-accent-primary border-accent-primary/30";
                } else if (isAssessed) {
                  badge = "Needs Focus";
                  badgeClass = "bg-accent-rose-subtle text-accent-rose border-accent-rose/30";
                }

                return (
                  <div key={skill.skill_id} className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-primary text-xs truncate max-w-[120px]">{skill.skill_name}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeClass}`}>
                        {badge}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted">Mastery</span>
                        <span className="font-bold text-primary">{isAssessed ? `${Math.round(skill.mastery_score * 100)}%` : "Not assessed"}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted">Confidence</span>
                        <span className="font-semibold text-accent-primary">{isAssessed ? `${Math.round(skill.confidence * 100)}%` : "Uncertain"}</span>
                      </div>
                    </div>

                    {priorRating && (
                      <div className="text-[11px] text-muted border-t border-subtle/50 pt-2">
                        Self-rated: <span className="font-semibold text-secondary">{priorRating}</span>
                      </div>
                    )}

                    <div className="text-[11px] text-muted">
                      {stats.attempted} questions • {stats.correct} correct
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Phase 14 Assessment History List */}
          {diagnosticHistory.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-subtle">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted">ASSESSMENT HISTORY</h3>
              <div className="divide-y divide-subtle/50 border border-subtle rounded-2xl overflow-hidden">
                {diagnosticHistory.map((item, idx) => (
                  <div key={item.session_id} className="p-3 bg-surface flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-primary">
                        {idx === 0 ? "Latest Diagnostic" : `Assessment #${diagnosticHistory.length - idx}`}
                      </span>
                      <span className="text-muted ml-2">
                        {new Date(item.started_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="text-muted font-medium">
                      {item.question_count} questions • {item.skills_count} skills
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-4 pt-4 border-t border-subtle">
            <Button
              variant="primary"
              size="md"
              onClick={() => (onNavigateToTab ? onNavigateToTab("path") : onDiagnosticComplete())}
            >
              Build My Adaptive Path →
            </Button>
            <Button
              variant="secondary"
              size="md"
              onClick={() => (onNavigateToTab ? onNavigateToTab("twin") : onDiagnosticComplete())}
            >
              See My Learning Twin →
            </Button>
            <Button
              variant="ghost"
              size="md"
              onClick={() => (onNavigateToTab ? onNavigateToTab("skills") : onDiagnosticComplete())}
            >
              View Bottleneck Analysis →
            </Button>
          </div>
        </div>
      </div>
    );
  }

  /* STAGE: NOT_STARTED */
  if (uiStage === "NOT_STARTED" || !question) {
    return (
      <div className="max-w-2xl mx-auto py-12 sm:py-16 text-center space-y-6 animate-in fade-in duration-300">
        <div className="bg-surface border border-subtle rounded-3xl p-8 sm:p-12 space-y-6 shadow-xs">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Adaptive Skill Assessment
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-primary tracking-tight uppercase">
            Let&apos;s Discover Your Current Skills
          </h2>
          <p className="text-secondary text-sm max-w-md mx-auto leading-relaxed">
            Your goal is active. Next, take an adaptive diagnostic check to measure your starting baseline across target role skills.
          </p>
          {errorMsg && (
            <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
              {errorMsg}
            </div>
          )}
          <Button variant="primary" size="lg" onClick={() => handleStartNewDiagnostic(false)}>
            Start Diagnostic →
          </Button>
        </div>
      </div>
    );
  }

  /* STAGE: IN_PROGRESS / EVALUATING / NEXT_QUESTION */
  const isCorrectFeedback = evaluation && evaluation.score >= 0.7;

  return (
    <div className="max-w-3xl mx-auto py-6 sm:py-8 space-y-6 animate-in fade-in duration-300">
      {/* Phase 3 & 22: Top Skill Calibration Header & Progress Pills */}
      <div className="space-y-4 bg-surface border border-subtle rounded-3xl p-5 shadow-xs">
        <div className="flex items-center justify-between text-xs font-bold text-primary">
          <span className="uppercase tracking-wider text-accent-primary">YOUR SKILL CALIBRATION</span>
          <span>Skills assessed {assessedSkillsCount} / {totalSkillsCount}</span>
        </div>

        {/* Progress Pills */}
        <div className="flex items-center justify-between gap-2">
          {Array.from({ length: question.total_questions }).map((_, i) => {
            const isAnswered = i < question.question_number - 1;
            const isCurrent = i === question.question_number - 1;
            return (
              <div
                key={i}
                className={`h-2.5 flex-1 rounded-full transition-all ${
                  isAnswered
                    ? "bg-accent-primary"
                    : isCurrent
                    ? "bg-accent-primary/50 animate-pulse ring-2 ring-accent-primary/30"
                    : "bg-subtle"
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Question Card Header */}
      <div className="flex items-center justify-between text-xs font-semibold text-secondary">
        <span>Question {question.question_number} of {question.total_questions}</span>
        <span className="px-3 py-1 rounded-full bg-subtle text-accent-primary border border-subtle font-bold">
          Skill: {question.skill_name} • Diff: {question.difficulty}/5
        </span>
      </div>

      {/* Question Card */}
      <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-10 shadow-xs space-y-6">
        <h2 className="text-xl sm:text-2xl font-extrabold text-primary leading-snug">
          {question.prompt}
        </h2>

        {/* Phase 8 Render by Question Type (MCQ, CODE, SHORT_TEXT) */}
        <div className="space-y-3">
          {question.question_type.toLowerCase() === "code" ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between bg-subtle/80 px-4 py-2 rounded-t-2xl border border-subtle text-xs text-muted font-mono">
                <span>{"// WRITE YOUR CODE ANSWER"}</span>
                <span>Python / Code Editor</span>
              </div>
              <textarea
                rows={6}
                value={selectedOption || ""}
                onChange={(e) => setSelectedOption(e.target.value)}
                placeholder="def solution():&#10;    # Write your code here..."
                className="w-full bg-subtle/30 font-mono border border-subtle rounded-b-2xl p-4 text-xs text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/30"
              />
            </div>
          ) : question.question_type.toLowerCase() === "short_text" ? (
            <textarea
              rows={4}
              value={selectedOption || ""}
              onChange={(e) => setSelectedOption(e.target.value)}
              placeholder="Explain your approach or short answer..."
              className="w-full bg-subtle/50 border border-subtle rounded-2xl p-4 text-sm text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/30"
            />
          ) : question.options && question.options.length > 0 ? (
            question.options.map((opt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setSelectedOption(opt)}
                className={`w-full text-left p-4 rounded-2xl border transition-all flex items-center space-x-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary ${
                  selectedOption === opt
                    ? "border-accent-primary bg-accent-primary/10 text-primary font-semibold shadow-xs"
                    : "border-subtle hover:border-hover bg-subtle/30 text-secondary"
                }`}
              >
                <span
                  className={`h-7 w-7 rounded-full border text-xs flex items-center justify-center font-bold shrink-0 transition-colors ${
                    selectedOption === opt
                      ? "border-accent-primary bg-accent-primary text-white"
                      : "border-subtle text-muted"
                  }`}
                >
                  {String.fromCharCode(65 + i)}
                </span>
                <span className="text-sm leading-relaxed">{opt}</span>
              </button>
            ))
          ) : (
            <input
              type="text"
              value={selectedOption || ""}
              onChange={(e) => setSelectedOption(e.target.value)}
              placeholder="Type your response..."
              className="w-full bg-subtle/50 border border-subtle rounded-2xl p-4 text-sm text-primary focus:outline-none focus:border-accent-primary"
            />
          )}
        </div>

        {/* Phase 5 & 9 Immediate Feedback & Adaptive Difficulty Indicator */}
        {evaluation && (
          <div
            className={`p-5 rounded-2xl border space-y-2 animate-in fade-in duration-200 ${
              isCorrectFeedback
                ? "bg-accent-mint-subtle/40 border-accent-mint/30"
                : "bg-accent-rose-subtle/40 border-accent-rose/30"
            }`}
          >
            <div className="flex items-center justify-between text-xs font-bold">
              <span className={isCorrectFeedback ? "text-accent-mint" : "text-accent-rose"}>
                {isCorrectFeedback ? "Correct (+ Diagnostic Evidence)" : "Needs Review"}
              </span>
              <span className="text-primary">Demonstrated Score: {Math.round(evaluation.score * 100)}%</span>
            </div>
            <p className="text-xs text-secondary leading-relaxed">{evaluation.feedback}</p>
            <p className="text-[11px] font-semibold text-muted pt-1 border-t border-subtle/40">
              {isCorrectFeedback
                ? "Your next question will be slightly more challenging."
                : "We'll use an easier question to better calibrate your level."}
            </p>
          </div>
        )}

        {errorMsg && (
          <div className="bg-accent-rose-subtle border border-accent-rose/30 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
            {errorMsg}
          </div>
        )}

        <div className="flex justify-between items-center pt-2 border-t border-subtle">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setUiStage("NOT_STARTED")}
          >
            ← Exit Diagnostic
          </Button>

          {!evaluation ? (
            <Button
              variant="primary"
              size="md"
              onClick={handleSubmitAnswer}
              disabled={!selectedOption || submitting}
            >
              {submitting ? "Evaluating..." : "Submit Answer →"}
            </Button>
          ) : (
            <Button
              variant="primary"
              size="md"
              onClick={() => loadNextQuestion(sessionId!)}
            >
              Next Question →
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
