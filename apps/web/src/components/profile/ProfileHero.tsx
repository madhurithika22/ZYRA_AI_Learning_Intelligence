"use client";

import React from "react";
import { LearnerProfileData } from "../../lib/types";
import { Button } from "../ui/Button";

interface ProfileHeroProps {
  profileData: LearnerProfileData;
  onEditProfile?: () => void;
  onDefineGoal?: () => void;
  onLogout?: () => void;
}

export function ProfileHero({
  profileData,
  onEditProfile,
  onDefineGoal,
  onLogout,
}: ProfileHeroProps) {
  const name = profileData.display_name;
  const email = profileData.email;

  // Explicit gender evaluation — never infer from name or email!
  const rawGender =
    profileData.profile?.avatar_gender?.toLowerCase() ||
    profileData.profile?.gender?.toLowerCase() ||
    null;
  const activeGender: string =
    rawGender && ["female", "male", "non_binary", "neutral"].includes(rawGender)
      ? rawGender
      : "neutral";

  // Goal & identity state
  const targetRole = profileData.current_journey?.target_role;

  // Gamification stats
  const level = profileData.gamification?.level ?? 1;
  const xp = profileData.gamification?.xp ?? 0;
  const nextLevelXp = profileData.gamification?.next_level_xp ?? 500;
  const levelProgressPct = profileData.gamification?.level_progress_pct ?? 0.0;
  const tier = profileData.gamification?.achievement_tier ?? "Explorer";

  // Profile config state
  const experienceLevel = profileData.profile?.experience_level;
  const learningMode = profileData.profile?.preferred_learning_mode;

  return (
    <div className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 md:p-10 shadow-lg relative overflow-hidden space-y-8">
      {/* Ambient background glow */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-accent-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Hero Editorial Grid: Large Avatar Left | Identity & Level Right */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center relative z-10">
        {/* LEFT / TOP: Large Avatar Presentation */}
        <div className="md:col-span-4 flex flex-col items-center justify-center text-center space-y-3">
          <div className="relative group">
            <div className="h-28 w-28 sm:h-36 sm:w-36 rounded-3xl bg-surface border-4 border-accent-primary/40 p-1.5 shadow-xl flex items-center justify-center relative overflow-hidden transition-all group-hover:border-accent-primary group-hover:scale-105">
              {activeGender === "female" && (
                <svg className="w-20 h-20 text-accent-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2a5 5 0 015 5v1a5 5 0 01-10 0V7a5 5 0 015-5zm0 12c-5.33 0-8 2.67-8 4v2h16v-2c0-1.33-2.67-4-8-4z" />
                  <path d="M12 4a3 3 0 00-3 3v.5a3.5 3.5 0 006 0V7a3 3 0 00-3-3z" opacity="0.3" />
                </svg>
              )}
              {activeGender === "male" && (
                <svg className="w-20 h-20 text-accent-indigo" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2a5 5 0 015 5v1a5 5 0 01-10 0V7a5 5 0 015-5zm0 12c-5.33 0-8 2.67-8 4v2h16v-2c0-1.33-2.67-4-8-4z" />
                </svg>
              )}
              {activeGender === "non_binary" && (
                <svg className="w-20 h-20 text-accent-mint" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2a5 5 0 015 5v1a5 5 0 01-10 0V7a5 5 0 015-5zm-7 16c0-1.33 2.67-4 8-4s8 2.67 8 4v2H5v-2z" />
                  <circle cx="12" cy="7" r="2" fill="white" />
                </svg>
              )}
              {activeGender === "neutral" && (
                <svg className="w-20 h-20 text-secondary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              )}
            </div>

            <span className="absolute -bottom-1 -right-1 px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-widest bg-surface border border-subtle text-secondary shadow-xs">
              {activeGender === "neutral" ? "Neutral" : activeGender.replace("_", "-")}
            </span>
          </div>

          <div className="space-y-1">
            <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
              {tier} Tier
            </span>
          </div>
        </div>

        {/* RIGHT: Identity Information & Level Progression */}
        <div className="md:col-span-8 space-y-5 text-left">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-primary tracking-tight">
                {name}
              </h1>
              <p className="text-xs font-bold uppercase tracking-widest text-accent-primary mt-1">
                Learning Intelligence Profile
              </p>
              <p className="text-xs text-muted font-medium mt-0.5">{email}</p>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              {onEditProfile && (
                <Button variant="primary" size="md" onClick={onEditProfile}>
                  Edit Profile
                </Button>
              )}
              {onLogout && (
                <Button variant="secondary" size="md" onClick={onLogout}>
                  Log Out
                </Button>
              )}
            </div>
          </div>

          {/* Role & Experience Metadata Badges */}
          <div className="flex items-center gap-2 flex-wrap text-xs">
            {targetRole ? (
              <span className="px-3 py-1.5 rounded-full font-bold bg-accent-primary text-white shadow-xs">
                🎯 {targetRole}
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-full font-bold bg-subtle text-secondary border border-subtle">
                No goal defined yet
              </span>
            )}

            {experienceLevel && (
              <span className="px-3 py-1.5 rounded-full font-semibold bg-accent-indigo/10 text-accent-indigo border border-accent-indigo/20">
                {experienceLevel}
              </span>
            )}
            {learningMode && (
              <span className="px-3 py-1.5 rounded-full font-semibold bg-subtle text-secondary border border-subtle">
                {learningMode} Mode
              </span>
            )}
          </div>

          {/* Level & XP Progression Strip */}
          <div className="bg-subtle/30 border border-subtle rounded-2xl p-4 sm:p-5 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-extrabold text-primary">LEVEL {level}</span>
              <span className="text-secondary font-medium">
                {xp.toLocaleString()} / {nextLevelXp.toLocaleString()} XP
              </span>
            </div>

            <div className="h-3 w-full bg-subtle rounded-full overflow-hidden p-0.5 border border-subtle/50">
              <div
                className="h-full bg-accent-primary rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, levelProgressPct))}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
