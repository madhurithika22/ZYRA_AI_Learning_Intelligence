"use client";

import React, { useState } from "react";
import { LearnerProfileData } from "../../lib/types";
import { Button } from "../ui/Button";
import { AvatarPicker } from "../identity/AvatarPicker";

interface ProfileEditFormProps {
  profileData: LearnerProfileData;
  onSave: (payload: {
    display_name: string;
    experience_level: string;
    preferred_learning_mode: string;
    weekly_availability_hours: number;
    stated_background: string;
    gender: string;
    avatar_gender?: string;
    avatar_variant?: string;
  }) => Promise<void>;
  onCancel: () => void;
  saving: boolean;
  error?: string | null;
}

export function ProfileEditForm({
  profileData,
  onSave,
  onCancel,
  saving,
  error,
}: ProfileEditFormProps) {
  const [displayName, setDisplayName] = useState<string>(profileData.display_name || "");
  const [email] = useState<string>(profileData.email || "");
  const [gender, setGender] = useState<string>(
    profileData.profile?.avatar_gender || profileData.profile?.gender || "neutral"
  );
  const [variant, setVariant] = useState<string>(
    profileData.profile?.avatar_variant || "classic"
  );
  const [experienceLevel, setExperienceLevel] = useState<string>(
    profileData.profile?.experience_level || "Intermediate"
  );
  const [preferredMode, setPreferredMode] = useState<string>(
    profileData.profile?.preferred_learning_mode || "Balanced"
  );
  const [weeklyHours, setWeeklyHours] = useState<number>(
    profileData.profile?.weekly_availability_hours || 10
  );
  const [background, setBackground] = useState<string>(
    profileData.profile?.stated_background || ""
  );

  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setValidationError(null);

    if (!displayName.trim()) {
      setValidationError("Display name is required.");
      return;
    }

    if (weeklyHours <= 0 || weeklyHours > 168) {
      setValidationError("Weekly availability must be between 1 and 168 hours.");
      return;
    }

    await onSave({
      display_name: displayName.trim(),
      experience_level: experienceLevel,
      preferred_learning_mode: preferredMode,
      weekly_availability_hours: Number(weeklyHours),
      stated_background: background,
      gender: gender,
      avatar_gender: gender,
      avatar_variant: variant,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface border border-subtle rounded-3xl p-6 sm:p-8 md:p-10 shadow-lg space-y-8"
    >
      <div className="border-b border-subtle pb-4 flex items-center justify-between">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Edit Account Preferences
          </span>
          <h2 className="text-2xl font-extrabold text-primary mt-1">Configure Profile</h2>
        </div>
        <Button variant="secondary" size="md" type="button" onClick={onCancel}>
          Cancel
        </Button>
      </div>

      {(validationError || error) && (
        <div className="bg-accent-rose/10 border border-accent-rose/20 rounded-2xl p-4 text-xs font-semibold text-accent-rose">
          {validationError || error}
        </div>
      )}

      {/* Avatar Picker Component */}
      <div className="bg-subtle/20 border border-subtle/50 p-5 rounded-2xl">
        <AvatarPicker
          gender={gender}
          variant={variant}
          onGenderChange={(g) => setGender(g)}
          onVariantChange={(v) => setVariant(v)}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Display Name */}
        <div>
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Display Name <span className="text-accent-rose">*</span>
          </label>
          <input
            type="text"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all"
            placeholder="e.g. Madhu Rithika"
          />
        </div>

        {/* Email (Read-only) */}
        <div>
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Email Address (Read-only)
          </label>
          <input
            type="email"
            disabled
            value={email}
            className="w-full bg-subtle/30 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-muted cursor-not-allowed"
          />
        </div>

        {/* Experience Level */}
        <div>
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Experience Level
          </label>
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all"
          >
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>

        {/* Preferred Learning Mode */}
        <div>
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Preferred Learning Mode
          </label>
          <select
            value={preferredMode}
            onChange={(e) => setPreferredMode(e.target.value)}
            className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all"
          >
            <option value="Theory First">Theory First</option>
            <option value="Balanced">Balanced</option>
            <option value="Project First">Project First</option>
            <option value="Fastest">Fastest</option>
          </select>
        </div>

        {/* Weekly Availability */}
        <div>
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Weekly Availability (Hours per week)
          </label>
          <input
            type="number"
            min={1}
            max={168}
            required
            value={weeklyHours}
            onChange={(e) => setWeeklyHours(Number(e.target.value))}
            className="w-full bg-subtle/50 border border-subtle rounded-2xl px-4 py-3.5 text-sm text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all"
          />
        </div>

        {/* Technical Background */}
        <div className="sm:col-span-2">
          <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
            Technical Background
          </label>
          <textarea
            rows={4}
            value={background}
            onChange={(e) => setBackground(e.target.value)}
            placeholder="Describe your current software engineering experience, known programming languages, frameworks, or past projects..."
            className="w-full bg-subtle/50 border border-subtle rounded-2xl p-4 text-sm text-primary placeholder-muted focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center justify-end space-x-4 pt-4 border-t border-subtle">
        <Button variant="secondary" size="md" type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="primary" size="md" type="submit" disabled={saving}>
          {saving ? "Saving Changes..." : "Save Changes"}
        </Button>
      </div>
    </form>
  );
}
