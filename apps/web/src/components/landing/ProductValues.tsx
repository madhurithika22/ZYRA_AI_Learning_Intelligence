"use client";

import React from "react";
import { Card } from "../ui/Card";

export function ProductValues() {
  const values = [
    {
      step: "01",
      title: "UNDERSTAND",
      description:
        "Know what you know — and how certain the system is.",
      badgeColor: "border-accent-primary text-accent-primary bg-accent-primary/5",
      accentDot: "bg-accent-primary",
    },
    {
      step: "02",
      title: "PRIORITIZE",
      description:
        "Focus on the skills that matter most for your goal.",
      badgeColor: "border-accent-sky text-accent-sky bg-accent-sky/5",
      accentDot: "bg-accent-sky",
    },
    {
      step: "03",
      title: "ADAPT",
      description:
        "Change the path as your demonstrated ability changes.",
      badgeColor: "border-accent-mint text-accent-mint bg-accent-mint/5",
      accentDot: "bg-accent-mint",
    },
  ];

  return (
    <section id="why-adaptive" className="py-12 sm:py-16 md:py-20 border-t border-subtle">
      <div className="space-y-12">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="text-xs font-bold uppercase tracking-widest text-muted">
            WHY ADAPTIVE
          </div>
          <h2 className="text-h1 font-extrabold text-primary tracking-tight">
            WHAT MAKES IT DIFFERENT?
          </h2>
          <p className="text-body text-secondary">
            Traditional learning treats everyone the same. Adaptive Learning Intelligence builds around your exact state.
          </p>
        </div>

        {/* 3 Value Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
          {values.map((val) => (
            <Card
              key={val.step}
              variant="elevated"
              className="p-6 sm:p-8 relative space-y-6 hover:border-accent-primary/40 transition-all duration-200 group flex flex-col justify-between"
            >
              <div className="space-y-4">
                {/* Number Badge & Title */}
                <div className="flex items-center justify-between">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${val.badgeColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${val.accentDot}`} />
                    {val.step}
                  </span>
                  <span className="text-xs font-bold tracking-widest text-muted uppercase">
                    {val.title}
                  </span>
                </div>

                <h3 className="text-h3 font-bold text-primary tracking-tight pt-2">
                  {val.title}
                </h3>

                <p className="text-body text-secondary leading-relaxed">
                  {val.description}
                </p>
              </div>

              {/* Bottom Decorative Line */}
              <div className="h-1 w-12 rounded-full bg-subtle group-hover:w-full group-hover:bg-accent-primary transition-all duration-300" />
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

