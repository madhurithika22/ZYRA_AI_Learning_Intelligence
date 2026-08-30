"use client";

import React from "react";

export type ProgressBarColor = "indigo" | "mint" | "sky" | "amber" | "rose";
export type ProgressBarSize = "sm" | "md" | "lg";

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  max?: number;
  color?: ProgressBarColor;
  size?: ProgressBarSize;
  showLabel?: boolean;
  labelPosition?: "right" | "top";
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  color = "indigo",
  size = "md",
  showLabel = false,
  labelPosition = "right",
  className = "",
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, Math.round((value / max) * 100)));

  const sizeStyles = {
    sm: "h-1.5 rounded-full",
    md: "h-2.5 rounded-full",
    lg: "h-4 rounded-full",
  }[size];

  const colorStyles = {
    indigo: "bg-accent-primary",
    mint: "bg-accent-mint",
    sky: "bg-accent-sky",
    amber: "bg-accent-amber",
    rose: "bg-accent-rose",
  }[color];

  return (
    <div className={`w-full space-y-1.5 ${className}`} {...props}>
      {showLabel && labelPosition === "top" && (
        <div className="flex justify-between items-center text-xs font-semibold text-secondary">
          <span>Progress</span>
          <span className="font-mono">{percentage}%</span>
        </div>
      )}
      <div className="flex items-center gap-3">
        <div className={`w-full bg-subtle overflow-hidden ${sizeStyles}`}>
          <div
            className={`h-full transition-all duration-500 ease-out rounded-full ${colorStyles}`}
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        {showLabel && labelPosition === "right" && (
          <span className="text-xs font-semibold text-secondary min-w-[36px] text-right font-mono">
            {percentage}%
          </span>
        )}
      </div>
    </div>
  );
}
