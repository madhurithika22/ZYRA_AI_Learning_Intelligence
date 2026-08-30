"use client";

import React from "react";

export type AvatarGender = "female" | "male" | "neutral" | "unspecified";
export type AvatarVariant = "default" | "profile" | "dashboard" | "compact";
export type AvatarSize = "sm" | "md" | "lg" | "xl" | "hero";

export interface LearnerAvatarProps {
  displayName?: string;
  avatarGender?: AvatarGender;
  variant?: AvatarVariant;
  size?: AvatarSize;
  className?: string;
  showBadge?: boolean;
}

export function LearnerAvatar({
  displayName = "Learner",
  avatarGender = "neutral",
  variant = "default",
  size = "md",
  className = "",
  showBadge = false,
}: LearnerAvatarProps) {
  const sizeMap: Record<AvatarSize, { box: string; icon: string; text: string }> = {
    sm: { box: "h-8 w-8 rounded-xl", icon: "w-4 h-4", text: "text-xs" },
    md: { box: "h-10 w-10 rounded-xl", icon: "w-5 h-5", text: "text-sm" },
    lg: { box: "h-12 w-12 rounded-2xl", icon: "w-6 h-6", text: "text-base" },
    xl: { box: "h-16 w-16 rounded-2xl", icon: "w-8 h-8", text: "text-xl" },
    hero: { box: "h-24 w-24 rounded-3xl", icon: "w-12 h-12", text: "text-3xl" },
  };

  const variantBorder = {
    default: "border-white/20",
    profile: "border-accent-primary ring-2 ring-accent-primary/20",
    dashboard: "border-subtle",
    compact: "border-transparent",
  }[variant];

  const initial = displayName && displayName.trim() ? displayName.trim()[0].toUpperCase() : "L";
  const { box, icon, text } = sizeMap[size];

  function renderAvatarContent() {
    if (avatarGender === "female") {
      return (
        <svg className={icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 14c-3.3 0-6 2.2-6 5v1h12v-1c0-2.8-2.7-5-6-5z" />
          <circle cx="12" cy="8" r="4" />
          <path strokeLinecap="round" d="M9 7c0-2 1.5-3.5 3-3.5s3 1.5 3 3.5" />
        </svg>
      );
    }
    if (avatarGender === "male") {
      return (
        <svg className={icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 14c-3.3 0-6 2.2-6 5v1h12v-1c0-2.8-2.7-5-6-5z" />
          <circle cx="12" cy="8" r="4" />
        </svg>
      );
    }
    return (
      <span className={`${text} font-extrabold tracking-tight`}>
        {initial}
      </span>
    );
  }

  return (
    <div className={`relative inline-flex items-center justify-center shrink-0 select-none ${className}`}>
      <div
        className={`${box} ${variantBorder} bg-gradient-to-br from-indigo-600 via-indigo-500 to-sky-500 text-white font-bold flex items-center justify-center shadow-xs border overflow-hidden`}
      >
        {renderAvatarContent()}
      </div>
      {showBadge && (
        <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-accent-mint border-2 border-surface" />
      )}
    </div>
  );
}
