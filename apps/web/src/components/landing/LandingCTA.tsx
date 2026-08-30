"use client";

import React from "react";
import { Button } from "../ui/Button";

interface LandingCTAProps {
  onStart: () => void;
}

export function LandingCTA({ onStart }: LandingCTAProps) {
  return (
    <section className="py-12 sm:py-16 md:py-20 border-t border-subtle">
      <div className="relative rounded-3xl p-8 sm:p-12 md:p-16 bg-surface border border-subtle text-center space-y-8 overflow-hidden shadow-lg">
        {/* Ambient Glow Backdrops */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-accent-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl mx-auto space-y-6">
          <span className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-subtle text-accent-primary text-xs font-bold uppercase tracking-wider">
            <span>GET STARTED TODAY</span>
          </span>

          <h2 className="text-display font-extrabold text-primary tracking-tight leading-tight">
            Your learning path should change as you do.
          </h2>

          <p className="text-body-lg text-secondary leading-relaxed">
            Experience an intelligence system designed to continuously evaluate evidence, address skill bottlenecks, and optimize your path.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={onStart}
              className="w-full sm:w-auto px-8 py-4 text-base font-bold shadow-md hover:shadow-lg transition-all"
            >
              Build My Learning Journey →
            </Button>
          </div>

          <p className="text-xs text-muted">
            Personalized to your goals, skills and evidence • Zero fluff
          </p>
        </div>
      </div>
    </section>
  );
}

