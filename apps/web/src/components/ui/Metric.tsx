"use client";

import React from "react";

export interface MetricProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  delta?: string | number;
  deltaType?: "positive" | "negative" | "neutral";
  icon?: React.ReactNode;
  hint?: string;
  className?: string;
}

export function Metric({
  label,
  value,
  delta,
  deltaType = "positive",
  icon,
  hint,
  className = "",
  ...props
}: MetricProps) {
  const deltaColor = {
    positive: "text-accent-mint bg-accent-mint-subtle",
    negative: "text-accent-rose bg-accent-rose-subtle",
    neutral: "text-secondary bg-subtle",
  }[deltaType];

  return (
    <div
      className={`bg-surface border border-subtle rounded-2xl p-5 shadow-xs flex flex-col justify-between space-y-3 ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between">
        <span className="text-caption font-semibold text-secondary uppercase tracking-wider">
          {label}
        </span>
        {icon && <div className="text-secondary p-1.5 rounded-xl bg-subtle">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="text-3xl font-extrabold text-primary tracking-tight font-sans">
          {value}
        </div>
        {delta !== undefined && (
          <div className={`px-2 py-0.5 rounded-full text-xs font-bold flex items-center gap-0.5 ${deltaColor}`}>
            <span>{deltaType === "positive" ? "↑" : deltaType === "negative" ? "↓" : "•"}</span>
            <span>{delta}</span>
          </div>
        )}
      </div>

      {hint && <p className="text-caption text-muted">{hint}</p>}
    </div>
  );
}
