"use client";

import React from "react";

export interface PillProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  count?: number;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function Pill({
  active = false,
  count,
  icon,
  className = "",
  children,
  ...props
}: PillProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-180 select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary ${
        active
          ? "bg-accent-primary text-white shadow-xs"
          : "bg-subtle/50 text-secondary hover:text-primary hover:bg-subtle border border-subtle/60"
      } ${className}`}
      {...props}
    >
      {icon}
      <span>{children}</span>
      {count !== undefined && (
        <span
          className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${
            active ? "bg-white/20 text-white" : "bg-surface text-muted"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );
}
