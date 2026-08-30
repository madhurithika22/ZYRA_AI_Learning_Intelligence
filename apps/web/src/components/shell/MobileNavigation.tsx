"use client";

import React from "react";
import { NavTabItem } from "./Navigation";

export interface MobileNavigationProps {
  navTabs: NavTabItem[];
  activeTab: string;
  isOpen: boolean;
  onSelectTab: (id: string) => void;
  className?: string;
}

export function MobileNavigation({
  navTabs,
  activeTab,
  isOpen,
  onSelectTab,
  className = "",
}: MobileNavigationProps) {
  if (!isOpen) return null;

  return (
    <div
      className={`lg:hidden border-t border-subtle mt-3 pt-3 pb-2 space-y-1.5 animate-in slide-in-from-top-2 duration-180 ${className}`}
    >
      {navTabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            aria-current={isActive ? "page" : undefined}
            className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center justify-between ${
              isActive
                ? "bg-accent-primary text-white font-bold shadow-xs"
                : "text-secondary hover:text-primary hover:bg-subtle"
            }`}
          >
            <span>{tab.label}</span>
            {isActive && <span>•</span>}
          </button>
        );
      })}
    </div>
  );
}
