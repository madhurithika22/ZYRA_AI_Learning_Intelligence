"use client";

import React from "react";

export function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Goal",
      desc: "Tell us where you want to go.",
    },
    {
      num: "02",
      title: "Diagnose",
      desc: "Discover what you already know.",
    },
    {
      num: "03",
      title: "Learn",
      desc: "Focus on the highest-impact gaps.",
    },
    {
      num: "04",
      title: "Prove",
      desc: "Demonstrate what you can actually do.",
    },
    {
      num: "05",
      title: "Adapt",
      desc: "Your next steps change as you improve.",
    },
  ];

  return (
    <section id="how-it-works" className="py-12 sm:py-16 md:py-20 border-t border-subtle">
      <div className="space-y-12 sm:space-y-16">
        {/* Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="text-xs font-bold uppercase tracking-widest text-muted">
            THE ADAPTIVE ENGINE
          </div>
          <h2 className="text-h1 font-extrabold text-primary tracking-tight">
            HOW IT WORKS
          </h2>
          <p className="text-body text-secondary">
            Continuous adaptation in 5 clear, evidence-grounded steps.
          </p>
        </div>

        {/* 5-Step Flow Grid */}
        <div className="relative">
          {/* Connecting Line (Desktop 1024px+) */}
          <div className="hidden lg:block absolute top-1/2 left-8 right-8 h-0.5 bg-subtle -translate-y-6 z-0" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 sm:gap-8 relative z-10">
            {steps.map((step, idx) => (
              <div
                key={step.num}
                className="p-6 rounded-2xl bg-surface border border-subtle hover:border-accent-primary/50 transition-all duration-200 space-y-4 shadow-xs group"
              >
                {/* Step Number & Connector indicator */}
                <div className="flex items-center justify-between">
                  <span className="text-h1 font-extrabold text-accent-primary/80 group-hover:text-accent-primary transition-colors font-mono">
                    {step.num}
                  </span>
                  <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-md bg-subtle text-muted">
                    Step {idx + 1}
                  </span>
                </div>

                <div className="space-y-2">
                  <h3 className="text-h3 font-bold text-primary tracking-tight">
                    {step.title}
                  </h3>
                  <p className="text-body-sm text-secondary leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

