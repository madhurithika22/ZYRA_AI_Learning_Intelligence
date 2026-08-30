"use client";

import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      iconLeft,
      iconRight,
      fullWidth = true,
      className = "",
      id,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;

    return (
      <div className={`space-y-1.5 ${fullWidth ? "w-full" : "inline-block"}`}>
        {label && (
          <label htmlFor={inputId} className="block text-xs font-bold text-primary select-none">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {iconLeft && (
            <div className="absolute left-3 text-muted pointer-events-none flex items-center">
              {iconLeft}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={`w-full bg-surface border rounded-xl px-3.5 py-2.5 text-sm text-primary placeholder:text-muted transition-all duration-180 focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent disabled:opacity-50 disabled:bg-subtle ${
              iconLeft ? "pl-10" : ""
            } ${iconRight ? "pr-10" : ""} ${
              error ? "border-accent-rose focus:ring-accent-rose" : "border-subtle hover:border-hover"
            } ${className}`}
            {...props}
          />
          {iconRight && (
            <div className="absolute right-3 text-muted pointer-events-none flex items-center">
              {iconRight}
            </div>
          )}
        </div>
        {error ? (
          <p className="text-xs font-semibold text-accent-rose">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-muted">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
