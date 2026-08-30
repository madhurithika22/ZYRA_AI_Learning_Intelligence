"use client";

import React from "react";
import { Button } from "./Button";

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`bg-accent-rose-subtle border border-rose-500/20 rounded-2xl p-6 sm:p-8 text-center flex flex-col items-center justify-center space-y-4 ${className}`}
    >
      <div className="p-3 rounded-full bg-accent-rose/10 text-accent-rose">
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      <div className="space-y-1 max-w-md">
        <h3 className="text-h3 font-bold text-accent-rose">{title}</h3>
        <p className="text-body-sm text-secondary">{message}</p>
      </div>

      {onRetry && (
        <Button variant="danger" size="sm" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
