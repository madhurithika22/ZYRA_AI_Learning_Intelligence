"use client";

import React from "react";

export interface DividerProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
  label?: string;
  className?: string;
}

export function Divider({
  orientation = "horizontal",
  label,
  className = "",
  ...props
}: DividerProps) {
  if (orientation === "vertical") {
    return (
      <div
        className={`inline-block w-[1px] self-stretch bg-border min-h-[1rem] ${className}`}
        role="separator"
        aria-orientation="vertical"
        {...props}
      />
    );
  }

  if (label) {
    return (
      <div
        className={`flex items-center w-full my-4 ${className}`}
        role="separator"
        aria-orientation="horizontal"
        {...props}
      >
        <div className="flex-1 border-t border-subtle" />
        <span className="px-3 text-caption font-semibold text-muted uppercase tracking-wider">
          {label}
        </span>
        <div className="flex-1 border-t border-subtle" />
      </div>
    );
  }

  return (
    <hr
      className={`w-full border-0 border-t border-subtle my-4 ${className}`}
      {...props}
    />
  );
}
