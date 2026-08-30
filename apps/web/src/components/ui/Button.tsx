"use client";

import React from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "success" | "outline";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  children?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled = false,
      iconLeft,
      iconRight,
      fullWidth = false,
      className = "",
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-semibold border transition-all duration-180 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98]";

    const sizeStyles: Record<ButtonSize, string> = {
      sm: "px-3 py-1.5 text-xs rounded-xl gap-1.5 h-8",
      md: "px-4.5 py-2.5 text-sm rounded-xl gap-2 h-10",
      lg: "px-6 py-3.5 text-base rounded-2xl gap-2.5 h-12",
    };

    const variantStyles: Record<ButtonVariant, string> = {
      primary:
        "bg-accent-primary hover:opacity-90 text-white border-transparent shadow-xs shadow-indigo-500/20 active:bg-accent-primary",
      secondary:
        "bg-surface border-subtle text-primary hover:bg-subtle hover:border-hover shadow-xs",
      ghost:
        "bg-transparent border-transparent text-secondary hover:text-primary hover:bg-subtle",
      danger:
        "bg-accent-rose hover:opacity-90 text-white border-transparent shadow-xs shadow-rose-500/20",
      success:
        "bg-accent-mint hover:opacity-90 text-white border-transparent shadow-xs shadow-emerald-500/20",
      outline:
        "bg-transparent border-subtle text-primary hover:bg-subtle hover:border-hover",
    };

    const widthClass = fullWidth ? "w-full" : "";

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${widthClass} ${className}`}
        {...props}
      >
        {isLoading ? (
          <span className="inline-block animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
        ) : (
          iconLeft
        )}
        {children && <span>{children}</span>}
        {!isLoading && iconRight}
      </button>
    );
  }
);

Button.displayName = "Button";
