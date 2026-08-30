"use client";

import React from "react";

export interface NavTabItem {
  id: string;
  label: string;
}

export interface NavigationProps {
  navTabs: NavTabItem[];
  activeTab: string;
  onSelectTab: (id: string) => void;
  className?: string;
}

export function Navigation({
  navTabs,
  activeTab,
  onSelectTab,
  className = "",
}: NavigationProps) {
  return (
    <nav
      role="navigation"
      aria-label="Main Application Navigation"
      className={`hidden lg:flex items-center gap-1 bg-subtle/40 p-1.5 rounded-2xl border border-subtle/70 ${className}`}
    >
      {navTabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            aria-current={isActive ? "page" : undefined}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-180 select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary ${
              isActive
                ? "bg-surface text-primary shadow-xs border border-subtle font-bold"
                : "text-secondary hover:text-primary hover:bg-surface/50"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
