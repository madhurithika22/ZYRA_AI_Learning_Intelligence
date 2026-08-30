"use client";

import React from "react";

export interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  align?: "left" | "center" | "between";
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  badge,
  action,
  align = "between",
  className = "",
}: SectionHeaderProps) {
  if (align === "center") {
    return (
      <div className={`text-center space-y-2 mb-6 ${className}`}>
        {badge && <div className="inline-flex justify-center mb-1">{badge}</div>}
        <h2 className="text-h2 font-bold text-primary tracking-snug">{title}</h2>
        {subtitle && <p className="text-body-sm text-secondary max-w-xl mx-auto">{subtitle}</p>}
        {action && <div className="pt-2">{action}</div>}
      </div>
    );
  }

  return (
    <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 ${className}`}>
      <div className="space-y-1">
        <div className="flex items-center gap-2.5">
          <h2 className="text-h2 font-bold text-primary tracking-snug">{title}</h2>
          {badge}
        </div>
        {subtitle && <p className="text-body-sm text-secondary">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0 flex items-center gap-2">{action}</div>}
    </div>
  );
}
