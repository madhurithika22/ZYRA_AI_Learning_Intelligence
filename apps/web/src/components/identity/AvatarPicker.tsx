"use client";

import React from "react";

interface AvatarPickerProps {
  gender: string;
  variant?: string;
  onGenderChange: (gender: string) => void;
  onVariantChange?: (variant: string) => void;
}

export function AvatarPicker({
  gender,
  variant = "classic",
  onGenderChange,
  onVariantChange,
}: AvatarPickerProps) {
  const genderOptions = [
    { id: "female", label: "Female", icon: "♀" },
    { id: "male", label: "Male", icon: "♂" },
    { id: "non_binary", label: "Non-binary / Other", icon: "✦" },
    { id: "neutral", label: "Prefer not to say (Neutral)", icon: "◯" },
  ];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-2">
          Gender / Avatar Preference
        </label>
        <p className="text-[11px] text-muted mb-3">
          Select your preferred identity presentation. Strictly used for explicit avatar presentation; never used to infer ability or learning.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {genderOptions.map((opt) => {
            const isSelected =
              gender === opt.id ||
              (opt.id === "neutral" && (gender === "prefer_not_to_say" || !gender));
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => onGenderChange(opt.id)}
                className={`p-3 rounded-2xl border text-xs font-bold transition-all flex flex-col items-center gap-1 text-center ${
                  isSelected
                    ? "bg-accent-primary/10 border-accent-primary text-accent-primary shadow-xs"
                    : "bg-subtle/30 border-subtle text-secondary hover:border-subtle/80 hover:bg-subtle/50"
                }`}
              >
                <span className="text-base">{opt.icon}</span>
                <span>{opt.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {onVariantChange && (
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-2">
            Avatar Style Variant
          </label>
          <div className="flex items-center gap-2">
            {["classic", "modern", "minimal"].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => onVariantChange(v)}
                className={`px-3 py-1.5 rounded-xl border text-xs font-semibold capitalize transition-all ${
                  variant === v
                    ? "bg-accent-indigo/10 border-accent-indigo text-accent-indigo font-bold"
                    : "bg-subtle/20 border-subtle text-secondary hover:bg-subtle/40"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
