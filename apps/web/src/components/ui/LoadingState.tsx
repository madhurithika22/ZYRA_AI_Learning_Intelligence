"use client";

import React from "react";

export interface LoadingStateProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  fullPage?: boolean;
  className?: string;
}

export function LoadingState({
  message = "Loading...",
  size = "md",
  fullPage = false,
  className = "",
}: LoadingStateProps) {
  const spinnerSize = {
    sm: "h-5 w-5 border-2",
    md: "h-8 w-8 border-3",
    lg: "h-12 w-12 border-4",
  }[size];

  const content = (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      <div
        className={`animate-spin ${spinnerSize} text-accent-primary border-current border-t-transparent rounded-full`}
      />
      {message && <p className="text-body-sm font-medium text-secondary">{message}</p>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center w-full p-8">
        {content}
      </div>
    );
  }

  return content;
}
