"use client";

import React from "react";

export function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 -z-50 pointer-events-none overflow-hidden select-none"
    >
      <div className="absolute -top-32 -right-32 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-indigo-500/10 via-sky-500/5 to-transparent blur-3xl opacity-70 dark:opacity-40" />
      <div className="absolute top-1/2 -left-40 w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-emerald-500/5 via-amber-500/5 to-transparent blur-3xl opacity-50 dark:opacity-30" />
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.03] dark:opacity-[0.05] text-primary"
        xmlns="http://www.w3.org/2000/svg"
      >
        <pattern id="node-grid-shell" width="40" height="40" patternUnits="userSpaceOnUse">
          <circle cx="20" cy="20" r="1.5" fill="currentColor" />
        </pattern>
        <rect width="100%" height="100%" fill="url(#node-grid-shell)" />
      </svg>
    </div>
  );
}
