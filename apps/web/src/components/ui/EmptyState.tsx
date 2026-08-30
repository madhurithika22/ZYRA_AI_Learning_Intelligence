"use client";

import React from "react";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`bg-surface border border-subtle border-dashed rounded-2xl p-8 sm:p-12 text-center flex flex-col items-center justify-center space-y-4 ${className}`}
    >
      {icon ? (
        <div className="p-4 rounded-2xl bg-subtle text-secondary">{icon}</div>
      ) : (
        <div className="p-4 rounded-2xl bg-subtle text-secondary">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
      )}

      <div className="space-y-1 max-w-sm">
        <h3 className="text-h3 font-bold text-primary">{title}</h3>
        {description && <p className="text-body-sm text-secondary">{description}</p>}
      </div>

      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
