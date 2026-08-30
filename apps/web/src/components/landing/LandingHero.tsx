"use client";

import React from "react";
import { Button } from "../ui/Button";
import { LearnerHeroAvatar } from "../identity/LearnerHeroAvatar";

interface LandingHeroProps {
  onStart: () => void;
  onLearnMore: () => void;
  gender?: "female" | "male" | "neutral" | string | null;
}

export function LandingHero({ onStart, onLearnMore, gender = "neutral" }: LandingHeroProps) {
  return (
    <section className="py-8 sm:py-12 md:py-16 lg:py-20 overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
        {/* Left Editorial Copy Column (55-60% width desktop) */}
        <div className="lg:col-span-7 space-y-6 sm:space-y-8 text-left z-10">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-subtle border border-subtle text-accent-primary text-xs font-bold uppercase tracking-wider">
            <span className="h-2 w-2 rounded-full bg-accent-primary animate-pulse" />
            <span>ADAPTIVE LEARNING INTELLIGENCE</span>
          </div>

          {/* Expressive Editorial Headline */}
          <h1 className="text-display-xl font-extrabold text-primary tracking-tight leading-[1.08]">
            Learn what you actually need.
            <span className="block mt-2 bg-gradient-to-r from-accent-primary via-accent-sky to-accent-rose bg-clip-text text-transparent">
              Adapt as you improve.
            </span>
          </h1>

          {/* Supporting Body Copy */}
          <p className="text-body-lg text-secondary max-w-xl font-normal leading-relaxed">
            Your learning journey continuously adjusts to your goals,
            demonstrated skills, evidence and progress — so you spend
            less time repeating what you already know and more time
            building what matters next.
          </p>

          {/* Call-to-Action Group */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
            <Button
              variant="primary"
              size="lg"
              onClick={onStart}
              className="w-full sm:w-auto text-base font-bold shadow-md hover:shadow-lg transition-all"
            >
              Start My Learning Journey →
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={onLearnMore}
              className="w-full sm:w-auto text-base font-semibold"
            >
              See How It Works →
            </Button>
          </div>

          {/* Trust Line */}
          <div className="flex items-center space-x-2 text-xs text-muted font-medium pt-1">
            <svg className="w-4 h-4 text-accent-mint shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            <span>Personalized to your goals, skills and evidence.</span>
          </div>
        </div>

        {/* Right 3D Student Hero Avatar Column */}
        <div className="lg:col-span-5 w-full flex justify-center lg:justify-end">
          <LearnerHeroAvatar gender={gender} variant="hero" size="hero" />
        </div>
      </div>
    </section>
  );
}

