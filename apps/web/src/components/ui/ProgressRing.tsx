"use client";

import React from "react";

export interface ProgressRingProps extends React.SVGAttributes<SVGSVGElement> {
  value: number; // 0 - 100
  size?: number;
  strokeWidth?: number;
  color?: "indigo" | "mint" | "sky" | "amber" | "rose";
  showValue?: boolean;
  className?: string;
}

export function ProgressRing({
  value,
  size = 64,
  strokeWidth = 6,
  color = "indigo",
  showValue = true,
  className = "",
  ...props
}: ProgressRingProps) {
  const percentage = Math.min(100, Math.max(0, Math.round(value)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const colorMap = {
    indigo: "var(--accent-primary)",
    mint: "var(--accent-mint)",
    sky: "var(--accent-sky)",
    amber: "var(--accent-amber)",
    rose: "var(--accent-rose)",
  };

  const strokeColor = colorMap[color];

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
        {...props}
      >
        {/* Background Track Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="opacity-40"
        />
        {/* Active Progress Radial Line */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {showValue && (
        <span className="absolute text-xs font-bold text-primary font-mono select-none">
          {percentage}%
        </span>
      )}
    </div>
  );
}
