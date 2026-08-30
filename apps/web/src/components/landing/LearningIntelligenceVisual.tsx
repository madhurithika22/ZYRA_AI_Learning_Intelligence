"use client";

import React from "react";
import { LearnerHeroAvatar } from "../identity/LearnerHeroAvatar";

interface LearningIntelligenceVisualProps {
  gender?: "female" | "male" | "neutral" | string | null;
}

export function LearningIntelligenceVisual({ gender = "neutral" }: LearningIntelligenceVisualProps) {
  return <LearnerHeroAvatar gender={gender} variant="hero" size="hero" />;
}
