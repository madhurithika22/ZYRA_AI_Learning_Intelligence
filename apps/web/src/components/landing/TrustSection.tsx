"use client";

import React from "react";
import { Card } from "../ui/Card";

export function TrustSection() {
  const principles = [
    {
      title: "Goal Alignment",
      description: "Learning sequences are anchored directly to your target role and stated objectives, eliminating irrelevant coursework.",
      icon: (
        <svg className="w-5 h-5 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      title: "Skill Mastery Tracking",
      description: "Continuous mathematical modeling of your demonstrated skill levels to keep difficulty in your optimal growth zone.",
      icon: (
        <svg className="w-5 h-5 text-accent-sky" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
        </svg>
      ),
    },
    {
      title: "Verifiable Evidence",
      description: "Recommendations require active proof through diagnostic assessments and practice evaluations, not self-reported assumptions.",
      icon: (
        <svg className="w-5 h-5 text-accent-mint" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      title: "Prerequisite Dependencies",
      description: "Prerequisite skill structures prevent premature progression and address root bottlenecks before moving forward.",
      icon: (
        <svg className="w-5 h-5 text-accent-amber" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      title: "Measured Progress",
      description: "Clear visualization of skill growth, confidence metrics, and remaining gap closure toward target competency.",
      icon: (
        <svg className="w-5 h-5 text-accent-rose" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
    },
    {
      title: "Demonstrated Outcomes",
      description: "Continuous replanning adapts your path dynamically whenever new mastery evidence or goal changes occur.",
      icon: (
        <svg className="w-5 h-5 text-accent-indigo" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
    },
  ];

  return (
    <section id="about-intelligence" className="py-12 sm:py-16 md:py-20 border-t border-subtle">
      <div className="space-y-12">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="text-xs font-bold uppercase tracking-widest text-muted">
            EVIDENCE-GROUNDED ARCHITECTURE
          </div>
          <h2 className="text-h1 font-extrabold text-primary tracking-tight">
            How Recommendations Are Formed
          </h2>
          <p className="text-body text-secondary">
            Every step suggested by the system is calculated using deterministic skill models and verified performance evidence.
          </p>
        </div>

        {/* 6 Grid Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {principles.map((item) => (
            <Card
              key={item.title}
              variant="elevated"
              className="p-6 space-y-3 hover:border-accent-primary/40 transition-all duration-200"
            >
              <div className="h-10 w-10 rounded-xl bg-subtle/80 flex items-center justify-center border border-subtle">
                {item.icon}
              </div>
              <h3 className="text-h3 font-bold text-primary tracking-tight pt-1">
                {item.title}
              </h3>
              <p className="text-body-sm text-secondary leading-relaxed">
                {item.description}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
