"use client";

import React from "react";

export type BadgeVariant = "primary" | "secondary" | "success" | "danger" | "warning" | "info" | "outline";
export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function Badge({
  variant = "primary",
  size = "md",
  icon,
  className = "",
  children,
  ...props
}: BadgeProps) {
  const sizeStyles = {
    sm: "px-2 py-0.5 text-[11px] font-semibold rounded-md gap-1",
    md: "px-2.5 py-1 text-xs font-bold rounded-lg gap-1.5",
  }[size];

  const variantStyles = {
    primary: "bg-accent-primary-subtle text-accent-primary border border-indigo-500/20",
    secondary: "bg-subtle text-secondary border border-subtle",
    success: "bg-accent-mint-subtle text-accent-mint border border-emerald-500/20",
    danger: "bg-accent-rose-subtle text-accent-rose border border-rose-500/20",
    warning: "bg-accent-amber-subtle text-accent-amber border border-amber-500/20",
    info: "bg-accent-sky-subtle text-accent-sky border border-sky-500/20",
    outline: "bg-transparent text-primary border border-subtle",
  }[variant];

  return (
    <span
      className={`inline-flex items-center justify-center transition-colors select-none ${sizeStyles} ${variantStyles} ${className}`}
      {...props}
    >
      {icon}
      <span>{children}</span>
    </span>
  );
}
