"use client";

import React, { useState } from "react";
import { useTheme } from "../../lib/theme";

export interface LearnerHeroAvatarProps {
  gender?: "female" | "male" | "neutral" | string | null;
  variant?: "hero" | "card" | "avatar";
  size?: "sm" | "md" | "lg" | "xl" | "hero";
  className?: string;
}

export function LearnerHeroAvatar({
  gender = "neutral",
  variant = "hero",
  size = "hero",
  className = "",
}: LearnerHeroAvatarProps) {
  const [imageError, setImageError] = useState(false);

  // Safely access Theme Context
  let resolvedTheme = "light";
  try {
    const themeContext = useTheme();
    resolvedTheme = themeContext.resolvedTheme;
  } catch {
    resolvedTheme = "light";
  }

  // Normalize gender strictly: default to "neutral" if unavailable or unspecified.
  const normalizedGender =
    gender === "female" ? "female" : gender === "male" ? "male" : "neutral";

  const lightImageSrc = `/avatars/hero_student_${normalizedGender}.jpg`;
  const darkImageSrc = `/avatars/hero_student_${normalizedGender}_dark.jpg`;

  const sizeClasses = {
    sm: "w-24 h-24",
    md: "w-40 h-40",
    lg: "w-64 h-64",
    xl: "w-80 h-80",
    hero: "w-full max-w-[480px] aspect-square",
  };

  return (
    <div className={`relative flex items-center justify-center ${sizeClasses[size]} ${className}`}>
      {/* Background Soft Pastel Ambient Glow (NO BOX CONTAINER AT ALL) */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-accent-primary/20 via-accent-sky/15 to-accent-rose/15 blur-3xl pointer-events-none" />

      {/* Floating Interactive Skill Badges around the Character (Safely contained bounds) */}
      {variant === "hero" && (
        <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden sm:overflow-visible">
          {/* Top Left Skill Node */}
          <div className="absolute top-3 left-2 bg-surface dark:bg-surface-elevated border border-subtle dark:border-border shadow-md px-3.5 py-1.5 rounded-full text-[11px] font-bold text-primary flex items-center gap-1.5 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-accent-primary" />
            <span>Goal Engine</span>
          </div>

          {/* Top Right Skill Node */}
          <div className="absolute top-4 right-2 bg-surface dark:bg-surface-elevated border border-subtle dark:border-border shadow-md px-3.5 py-1.5 rounded-full text-[11px] font-bold text-primary flex items-center gap-1.5 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-accent-mint" />
            <span>Diagnostic 94%</span>
          </div>

          {/* Mid Right Floating Badge */}
          <div className="absolute bottom-24 right-2 hidden sm:flex bg-surface dark:bg-surface-elevated border border-subtle dark:border-border shadow-md px-3.5 py-1.5 rounded-full text-[11px] font-bold text-accent-sky items-center gap-1.5 backdrop-blur-md">
            <span>Adaptive Path →</span>
          </div>

          {/* Bottom Left Mastery Badge */}
          <div className="absolute bottom-4 left-2 bg-surface dark:bg-surface-elevated border border-subtle dark:border-border shadow-md px-3.5 py-1.5 rounded-full text-[11px] font-bold text-primary flex items-center gap-1.5 backdrop-blur-md">
            <span className="text-accent-rose font-mono font-extrabold">f(x)</span>
            <span>Mastery Proven</span>
          </div>
        </div>
      )}

      {/* Main 3D Character (ABSOLUTELY NO CONTAINER BOX / NO BORDER / NO WHITE BACKGROUND) */}
      <div className="relative z-10 w-full h-full flex items-center justify-center">
        {!imageError ? (
          <>
            {/* Render active theme image and CSS fallback for instant switching */}
            <img
              src={resolvedTheme === "dark" ? darkImageSrc : lightImageSrc}
              alt={`Adaptive Learning 3D Student Avatar (${normalizedGender})`}
              onError={() => setImageError(true)}
              className="w-full h-full object-contain rounded-3xl transition-transform duration-500 hover:scale-102 pointer-events-none"
            />
          </>
        ) : (
          /* SVG Vector 3D Character Fallback */
          <div className="w-full h-full flex flex-col items-center justify-center p-8">
            <svg className="w-48 h-48" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="100" cy="100" r="80" fill="var(--subtle)" />
              <circle cx="100" cy="70" r="30" fill="var(--accent-primary)" opacity="0.8" />
              <path d="M 50 140 C 50 110, 70 95, 100 95 C 130 95, 150 110, 150 140 Z" fill="var(--accent-primary)" opacity="0.8" />
            </svg>
            <span className="text-xs font-semibold text-muted mt-2">
              Learner Avatar ({normalizedGender})
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
