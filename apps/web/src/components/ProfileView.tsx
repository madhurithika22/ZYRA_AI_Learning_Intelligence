"use client";

import React, { useState, useEffect } from "react";
import { AuthUser, LearnerProfileData } from "../lib/types";
import { fetchLearnerProfile, updateLearnerProfile } from "../lib/api";
import { ProfileHero } from "./profile/ProfileHero";
import { ProfileEditForm } from "./profile/ProfileEditForm";
import { Button } from "./ui/Button";

interface ProfileViewProps {
  user: AuthUser;
  onLogout: () => void;
  onProfileUpdated?: (updatedName: string) => void;
  onDefineGoal?: () => void;
}

export function ProfileView({
  user,
  onLogout,
  onProfileUpdated,
  onDefineGoal,
}: ProfileViewProps) {
  const [profileData, setProfileData] = useState<LearnerProfileData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchLearnerProfile(user.learner_id);
        if (!active) return;
        setProfileData(data);
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : "Failed to load learner profile.";
        setError(msg);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [user.learner_id, user.display_name]);

  // Phase 12: Profile Editing UX - Refetches authoritative profile state after POST/PUT save
  async function handleSave(payload: {
    display_name: string;
    experience_level: string;
    preferred_learning_mode: string;
    weekly_availability_hours: number;
    stated_background: string;
    gender: string;
    avatar_gender?: string;
    avatar_variant?: string;
  }) {
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await updateLearnerProfile(user.learner_id, payload);
      // Authoritative GET refetch — no optimistic state assumptions!
      const freshProfile = await fetchLearnerProfile(user.learner_id);
      setProfileData(freshProfile);
      setEditing(false);
      setSuccessMsg("Profile updated successfully!");
      if (onProfileUpdated) {
        onProfileUpdated(freshProfile.display_name);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update profile.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center space-y-4">
        <div className="inline-block animate-spin h-8 w-8 text-accent-primary border-4 border-current border-t-transparent rounded-full" />
        <p className="text-secondary text-sm font-medium">Loading Learning Intelligence Profile...</p>
      </div>
    );
  }

  const currentStreak = profileData?.gamification?.current_streak ?? profileData?.gamification?.streak_days ?? 0;
  const longestStreak = profileData?.gamification?.longest_streak ?? currentStreak;
  const level = profileData?.gamification?.level ?? 1;
  const achievementTier = profileData?.gamification?.achievement_tier ?? "Explorer";
  const xp = profileData?.gamification?.xp ?? 0;
  const evidenceCount = profileData?.gamification?.evidence_count ?? 0;

  // Phase 9: Weekly Activity Strip
  const weeklyStrip = profileData?.gamification?.weekly_activity_strip || [
    { day: "M", date: "", active: false, is_today: false },
    { day: "T", date: "", active: false, is_today: false },
    { day: "W", date: "", active: false, is_today: false },
    { day: "T", date: "", active: false, is_today: false },
    { day: "F", date: "", active: false, is_today: false },
    { day: "S", date: "", active: false, is_today: false },
    { day: "S", date: "", active: false, is_today: false },
  ];
  const weeklyActiveDaysCount = profileData?.gamification?.weekly_active_days_count ?? 0;
  const todayActive = profileData?.gamification?.today_active ?? false;

  // Phase 10: Strengths & Growth Areas
  const strengths = profileData?.gamification?.strengths || [];
  const growthAreas = profileData?.gamification?.growth_areas || [];

  // Phase 11: Personal Learning Identity Summary
  const identitySummary = profileData?.gamification?.identity_summary;
  const targetRole = identitySummary?.target_role || profileData?.current_journey?.target_role || "Learning Journey";
  const strongestSkill = identitySummary?.strongest_skill || (strengths.length > 0 ? strengths[0] : "Assessment in progress");
  const biggestOpportunity = identitySummary?.biggest_opportunity || (growthAreas.length > 0 ? growthAreas[0] : "Initial diagnostic evaluation");

  // Phase 15: Empty Profile Evaluation
  const isEmptyProfile = (profileData?.goals_count === 0) && (xp === 0) && (evidenceCount === 0);

  const achievements = profileData?.gamification?.achievements || [
    { id: "first_step", title: "FIRST STEP", description: "Defined your first learning goal.", condition: "Create at least 1 career goal", unlocked: (profileData?.goals_count || 0) > 0, earned_at: null, icon: "target" },
    { id: "diagnostic_complete", title: "DIAGNOSTIC COMPLETE", description: "Completed your first adaptive assessment.", condition: "Complete diagnostic knowledge mapping", unlocked: false, earned_at: null, icon: "clipboard" },
    { id: "first_proof", title: "FIRST PROOF", description: "Submitted your first mastery evidence.", condition: "Submit a mastery check assessment", unlocked: false, earned_at: null, icon: "award" },
    { id: "skill_demonstrated", title: "SKILL DEMONSTRATED", description: "Proved mastery in a target skill.", condition: "Achieve >= 80% mastery score in a skill", unlocked: false, earned_at: null, icon: "zap" },
    { id: "consistent_learner", title: "CONSISTENT LEARNER", description: "Maintained a 7-day learning streak.", condition: "Maintain a streak of 7 consecutive active days", unlocked: false, earned_at: null, icon: "flame" },
    { id: "path_adapter", title: "PATH ADAPTER", description: "Accepted your first dynamically replanned path.", condition: "Accept a dynamically adapted learning path", unlocked: false, earned_at: null, icon: "git-branch" },
    { id: "evidence_builder", title: "EVIDENCE BUILDER", description: "Recorded 5 verified learning outcomes.", condition: "Accumulate 5 verified skill evidence entries", unlocked: false, earned_at: null, icon: "shield" },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8">
      {error && (
        <div className="bg-accent-rose/10 border border-accent-rose/20 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="bg-accent-mint/10 border border-accent-mint/20 rounded-2xl p-4 text-xs font-semibold text-accent-mint">
          {successMsg}
        </div>
      )}

      {!editing ? (
        <div className="space-y-8">
          {/* Phase 15: Empty Profile Banner for New Users */}
          {isEmptyProfile && (
            <div className="bg-accent-primary/10 border border-accent-primary/30 rounded-3xl p-6 sm:p-8 space-y-4">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                  YOUR LEARNING PROFILE
                </span>
                <h2 className="text-xl sm:text-2xl font-extrabold text-primary">
                  You haven&apos;t started your learning journey yet.
                </h2>
                <p className="text-xs text-secondary">
                  Complete your profile, define your target career goal, take your diagnostic, and build your adaptive path.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2">
                <Button variant="primary" size="md" onClick={() => setEditing(true)}>
                  1. Complete Profile
                </Button>
                {onDefineGoal && (
                  <Button variant="secondary" size="md" onClick={onDefineGoal}>
                    2. Define Goal
                  </Button>
                )}
                <div className="p-3 bg-surface border border-subtle rounded-2xl text-center text-xs font-bold text-muted flex items-center justify-center">
                  3. Diagnostic
                </div>
                <div className="p-3 bg-surface border border-subtle rounded-2xl text-center text-xs font-bold text-muted flex items-center justify-center">
                  4. Adaptive Path
                </div>
              </div>
            </div>
          )}

          {/* Phase 8: Profile Hero Component */}
          {profileData && (
            <ProfileHero
              profileData={profileData}
              onEditProfile={() => setEditing(true)}
              onDefineGoal={onDefineGoal}
              onLogout={onLogout}
            />
          )}

          {/* Phase 9: Daily Learning Streak (7-Day Activity Strip) */}
          <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
            <div className="border-b border-subtle pb-3 flex items-center justify-between flex-wrap gap-2">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                  THIS WEEK ACTIVITY
                </span>
                <h3 className="text-lg font-extrabold text-primary mt-0.5">7-Day Engagement Strip</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-extrabold px-3 py-1 rounded-full border ${
                  todayActive
                    ? "bg-accent-mint/10 text-accent-mint border-accent-mint/20"
                    : "bg-subtle text-secondary border-subtle"
                }`}>
                  Today: {todayActive ? "Active ●" : "No activity yet ○"}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between max-w-md mx-auto py-2">
                {weeklyStrip.map((item, idx) => (
                  <div key={idx} className="flex flex-col items-center space-y-2">
                    <span className="text-xs font-extrabold text-secondary">{item.day}</span>
                    <div
                      className={`h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                        item.active
                          ? "bg-accent-primary text-white shadow-md scale-105"
                          : "bg-subtle/50 text-muted border border-subtle"
                      } ${item.is_today ? "ring-2 ring-accent-primary ring-offset-2 ring-offset-surface" : ""}`}
                    >
                      {item.active ? "●" : "○"}
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-center text-xs font-semibold text-secondary">
                {weeklyActiveDaysCount} active learning days this week
              </p>
            </div>

            {/* Streak & Engagement Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center pt-2">
              <div className="bg-subtle/40 border border-subtle rounded-2xl p-4 sm:p-5 space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center justify-center gap-1">
                  <span>🔥</span> Current Streak
                </span>
                <p className="text-2xl sm:text-3xl font-extrabold text-primary">
                  {currentStreak} <span className="text-xs font-normal text-secondary">days</span>
                </p>
                <p className="text-[11px] text-muted font-medium">
                  Longest streak: {longestStreak} {longestStreak === 1 ? "day" : "days"}
                </p>
              </div>

              <div className="bg-subtle/40 border border-subtle rounded-2xl p-4 sm:p-5 space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                  Level
                </span>
                <p className="text-2xl sm:text-3xl font-extrabold text-accent-primary">
                  {level}
                </p>
                <p className="text-[11px] text-muted font-medium">{achievementTier} Tier</p>
              </div>

              <div className="bg-subtle/40 border border-subtle rounded-2xl p-4 sm:p-5 space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-secondary">
                  Evidence
                </span>
                <p className="text-2xl sm:text-3xl font-extrabold text-primary">
                  {evidenceCount}
                </p>
                <p className="text-[11px] text-muted font-medium">Verified skill proof</p>
              </div>
            </div>
          </div>

          {/* Phase 10: Learning Identity — Strengths & Growth Areas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-4">
              <div className="border-b border-subtle pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-accent-mint">
                  DEMONSTRATED STRENGTHS
                </span>
                <h3 className="text-lg font-extrabold text-primary mt-0.5">My Strengths</h3>
              </div>

              {strengths.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {strengths.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-accent-mint/10 text-accent-mint border border-accent-mint/20"
                    >
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-secondary italic">
                  No high-mastery skills demonstrated yet. Complete learning activities & mastery checks to highlight your strengths.
                </p>
              )}
            </div>

            {/* Growth Areas */}
            <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-4">
              <div className="border-b border-subtle pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-accent-amber">
                  GROWTH OPPORTUNITIES
                </span>
                <h3 className="text-lg font-extrabold text-primary mt-0.5">Current Growth Areas</h3>
              </div>

              {growthAreas.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {growthAreas.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-accent-amber/10 text-accent-amber border border-accent-amber/20"
                    >
                      ⚡ {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-secondary italic">
                  No current skill gaps detected.
                </p>
              )}
            </div>
          </div>

          {/* Phase 11: Personal Learning Summary ("YOUR LEARNING IDENTITY") */}
          <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-5">
            <div className="border-b border-subtle pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                PERSONAL LEARNING SUMMARY
              </span>
              <h3 className="text-xl font-extrabold text-primary mt-0.5">YOUR LEARNING IDENTITY</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-1">
                <span className="text-[11px] font-semibold text-muted uppercase">Target Career Role</span>
                <p className="font-extrabold text-primary text-sm">
                  You&apos;re currently building toward: <span className="text-accent-primary">{targetRole}</span>
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-1">
                <span className="text-[11px] font-semibold text-muted uppercase">Strongest Demonstrated Skill</span>
                <p className="font-extrabold text-primary text-sm">
                  Your strongest demonstrated skill: <span className="text-accent-mint">{strongestSkill}</span>
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-1">
                <span className="text-[11px] font-semibold text-muted uppercase">Biggest Opportunity</span>
                <p className="font-extrabold text-primary text-sm">
                  Your biggest opportunity: <span className="text-accent-amber">{biggestOpportunity}</span>
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-subtle/30 border border-subtle space-y-1">
                <span className="text-[11px] font-semibold text-muted uppercase">Current Consistency & Proof</span>
                <p className="font-extrabold text-primary text-sm">
                  {weeklyActiveDaysCount} active days this week • {evidenceCount} verified outcomes
                </p>
              </div>
            </div>
          </div>

          {/* Phase 14 Anchor: ACHIEVEMENTS */}
          <div id="achievements" className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 scroll-mt-20">
            <div className="border-b border-subtle pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                ACHIEVEMENTS
              </span>
              <h3 className="text-lg font-extrabold text-primary mt-1">Unlocked & Milestone Badges</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {achievements.map((badge) => {
                const isUnlocked = badge.unlocked;
                const earnedDateStr = badge.earned_at || badge.unlocked_at;
                let formattedDate = "";
                if (earnedDateStr) {
                  try {
                    formattedDate = new Date(earnedDateStr).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    });
                  } catch {
                    formattedDate = "";
                  }
                }

                return (
                  <div
                    key={badge.id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col justify-between space-y-3 ${
                      isUnlocked
                        ? "bg-accent-primary/5 border-accent-primary/30"
                        : "bg-subtle/20 border-subtle/40 opacity-75"
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div
                        className={`h-9 w-9 rounded-xl flex items-center justify-center shrink-0 font-bold text-sm ${
                          isUnlocked
                            ? "bg-accent-primary text-white shadow-sm"
                            : "bg-subtle/80 text-muted border border-subtle"
                        }`}
                      >
                        {isUnlocked ? "✓" : "🔒"}
                      </div>
                      <div className="space-y-0.5 min-w-0">
                        <h4 className="text-xs font-extrabold tracking-wide text-primary uppercase">
                          {badge.title}
                        </h4>
                        <p className="text-[11px] text-secondary leading-snug">{badge.description}</p>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-subtle/40 flex items-center justify-between text-[10px] font-medium text-muted">
                      <span className="truncate max-w-[140px] text-secondary/80">{badge.condition}</span>
                      <span className={isUnlocked ? "text-accent-primary font-semibold" : "text-muted"}>
                        {isUnlocked
                          ? formattedDate
                            ? `Earned ${formattedDate}`
                            : "Earned"
                          : "○ Not yet earned"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Phase 14 Anchor: LEARNING PREFERENCES */}
          <div id="preferences" className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 shadow-xs space-y-6 scroll-mt-20">
            <div className="border-b border-subtle pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
                LEARNING PREFERENCES
              </span>
              <h3 className="text-lg font-extrabold text-primary mt-1">Personalized Settings</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-sm">
              <div>
                <span className="text-xs text-muted block font-semibold uppercase tracking-wider">
                  Experience Level
                </span>
                <span className="font-semibold text-primary mt-1 block">
                  {profileData?.profile?.experience_level || "Not specified"}
                </span>
              </div>

              <div>
                <span className="text-xs text-muted block font-semibold uppercase tracking-wider">
                  Learning Mode
                </span>
                <span className="font-semibold text-primary mt-1 block">
                  {profileData?.profile?.preferred_learning_mode || "Not specified"}
                </span>
              </div>

              <div>
                <span className="text-xs text-muted block font-semibold uppercase tracking-wider">
                  Weekly Availability
                </span>
                <span className="font-semibold text-primary mt-1 block">
                  {profileData?.profile?.weekly_availability_hours || 10} hours / week
                </span>
              </div>
            </div>

            <div className="pt-2 border-t border-subtle">
              <span className="text-xs text-muted block font-semibold uppercase tracking-wider mb-1">
                Stated Technical Background
              </span>
              <p className="text-xs text-secondary leading-relaxed bg-subtle/30 border border-subtle p-3.5 rounded-2xl">
                {profileData?.profile?.stated_background || "No background details specified yet."}
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Edit Profile Form Component */
        profileData && (
          <ProfileEditForm
            profileData={profileData}
            onSave={handleSave}
            onCancel={() => setEditing(false)}
            saving={saving}
            error={error}
          />
        )
      )}
    </div>
  );
}
