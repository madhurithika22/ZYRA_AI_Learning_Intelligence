"use client";

import React from "react";
import { Tooltip } from "./Tooltip";

export type IconButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "outline";
export type IconButtonSize = "sm" | "md" | "lg";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  "aria-label": string;
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  tooltip?: string;
  isLoading?: boolean;
  className?: string;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      "aria-label": ariaLabel,
      variant = "secondary",
      size = "md",
      tooltip,
      isLoading = false,
      disabled = false,
      className = "",
      ...props
    },
    ref
  ) => {
    const sizeStyles = {
      sm: "h-8 w-8 p-1.5 rounded-xl text-xs",
      md: "h-10 w-10 p-2 rounded-xl text-sm",
      lg: "h-12 w-12 p-3 rounded-2xl text-base",
    }[size];

    const variantStyles = {
      primary: "bg-accent-primary text-white hover:opacity-90 border border-transparent shadow-xs",
      secondary: "bg-surface border border-subtle text-secondary hover:text-primary hover:bg-subtle shadow-xs",
      ghost: "bg-transparent border border-transparent text-secondary hover:text-primary hover:bg-subtle",
      danger: "bg-accent-rose-subtle border border-rose-500/20 text-accent-rose hover:bg-accent-rose hover:text-white",
      outline: "bg-transparent border border-subtle text-primary hover:bg-subtle",
    }[variant];

    const buttonElement = (
      <button
        ref={ref}
        aria-label={ariaLabel}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center font-semibold transition-all duration-180 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.96] ${sizeStyles} ${variantStyles} ${className}`}
        {...props}
      >
        {isLoading ? (
          <span className="inline-block animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
        ) : (
          icon
        )}
      </button>
    );

    if (tooltip) {
      return <Tooltip content={tooltip}>{buttonElement}</Tooltip>;
    }

    return buttonElement;
  }
);

IconButton.displayName = "IconButton";
