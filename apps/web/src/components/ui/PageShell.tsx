"use client";

import React from "react";

export type PageShellVariant = "default" | "wide" | "narrow" | "full";

export interface PageShellProps {
  children: React.ReactNode;
  /** Controls max-width of inner container: narrow (~768px), default (~1152px), wide (~1440px), full (100%) */
  variant?: PageShellVariant;
  /** Toggles subtle ambient background mesh glow */
  decorativeGlow?: boolean;
  /** Outer canvas wrapper additional CSS classes */
  className?: string;
  /** Inner content container additional CSS classes */
  containerClassName?: string;
  /** Optional sticky or static header element */
  header?: React.ReactNode;
  /** Optional footer element */
  footer?: React.ReactNode;
}

export function PageShell({
  children,
  variant = "wide",
  decorativeGlow = true,
  className = "",
  containerClassName = "",
  header,
  footer,
}: PageShellProps) {
  const maxWidthClass = {
    narrow: "max-w-3xl",       // Focused forms / single column (~768px)
    default: "max-w-6xl",      // Standard editorial content (~1152px)
    wide: "max-w-[1440px]",    // Full-featured wide dashboards & 3-column layouts (~1440px)
    full: "max-w-none w-full", // Full-width canvas & timelines (100%)
  }[variant];

  return (
    <div
      className={`min-h-screen bg-background text-primary relative overflow-x-hidden flex flex-col font-sans transition-colors duration-200 ${className}`}
    >
      {/* Decorative Ambient Mesh Background Layer */}
      {decorativeGlow && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 overflow-hidden select-none"
        >
          {/* Top-Right Soft Indigo Glow */}
          <div className="absolute -top-40 -right-20 w-[550px] h-[550px] rounded-full bg-gradient-to-br from-indigo-500/10 via-sky-500/5 to-transparent blur-3xl opacity-70 dark:opacity-40" />

          {/* Center-Left Soft Mint/Amber Glow */}
          <div className="absolute top-1/3 -left-32 w-[450px] h-[450px] rounded-full bg-gradient-to-tr from-emerald-500/5 via-amber-500/5 to-transparent blur-3xl opacity-50 dark:opacity-25" />
        </div>
      )}

      {/* Header Slot */}
      {header && <header className="w-full shrink-0 z-40">{header}</header>}

      {/* Responsive Application Canvas Main Content Area */}
      <main
        className={`flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 py-6 md:py-10 space-y-8 ${maxWidthClass} ${containerClassName}`}
      >
        {children}
      </main>

      {/* Footer Slot */}
      {footer && <footer className="w-full shrink-0 mt-auto">{footer}</footer>}
    </div>
  );
}

/* ==================================================
   REUSABLE CANVAS LAYOUT PRIMITIVES
   ================================================== */

export interface TwoColumnLayoutProps {
  main: React.ReactNode;
  sidebar: React.ReactNode;
  /** Sidebar position: 'right' (default) or 'left' */
  sidebarPosition?: "right" | "left";
  className?: string;
}

/** 2-Column Responsive Layout Grid (Main Content + Sidebar) */
export function TwoColumnLayout({
  main,
  sidebar,
  sidebarPosition = "right",
  className = "",
}: TwoColumnLayoutProps) {
  return (
    <div className={`grid grid-cols-1 lg:grid-cols-12 gap-8 items-start ${className}`}>
      {sidebarPosition === "left" && (
        <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">{sidebar}</aside>
      )}
      <section className="lg:col-span-8 space-y-6">{main}</section>
      {sidebarPosition === "right" && (
        <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">{sidebar}</aside>
      )}
    </div>
  );
}

export interface ThreeColumnLayoutProps {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
  className?: string;
}

/** 3-Column Responsive Dashboard Layout Grid */
export function ThreeColumnLayout({
  left,
  center,
  right,
  className = "",
}: ThreeColumnLayoutProps) {
  return (
    <div className={`grid grid-cols-1 lg:grid-cols-12 gap-6 items-start ${className}`}>
      <aside className="lg:col-span-3 space-y-6">{left}</aside>
      <section className="lg:col-span-6 space-y-6">{center}</section>
      <aside className="lg:col-span-3 space-y-6">{right}</aside>
    </div>
  );
}

export interface FocusedFormContainerProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}

/** Focused Single-Column Form Layout Container */
export function FocusedFormContainer({
  children,
  title,
  subtitle,
  className = "",
}: FocusedFormContainerProps) {
  return (
    <div className={`max-w-xl mx-auto space-y-6 ${className}`}>
      {(title || subtitle) && (
        <div className="text-center space-y-2">
          {title && <h1 className="text-h1 text-primary">{title}</h1>}
          {subtitle && <p className="text-body-sm text-secondary">{subtitle}</p>}
        </div>
      )}
      <div className="bg-surface border border-subtle rounded-2xl p-6 sm:p-8 shadow-sm">
        {children}
      </div>
    </div>
  );
}
