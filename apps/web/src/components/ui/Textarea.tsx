"use client";

import React from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  className?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = true,
      className = "",
      id,
      rows = 4,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const textareaId = id || generatedId;

    return (
      <div className={`space-y-1.5 ${fullWidth ? "w-full" : "inline-block"}`}>
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-bold text-primary select-none">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          rows={rows}
          className={`w-full bg-surface border rounded-xl p-3.5 text-sm text-primary placeholder:text-muted transition-all duration-180 focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent disabled:opacity-50 disabled:bg-subtle ${
            error ? "border-accent-rose focus:ring-accent-rose" : "border-subtle hover:border-hover"
          } ${className}`}
          {...props}
        />
        {error ? (
          <p className="text-xs font-semibold text-accent-rose">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-muted">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";
