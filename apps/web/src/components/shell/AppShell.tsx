"use client";

import React from "react";
import { AuthUser, LearnerAppStateResponse } from "../../lib/types";
import { Header } from "./Header";
import { AmbientBackground } from "./AmbientBackground";
import { JourneyIndicator } from "../JourneyIndicator";

export interface AppShellProps {
  user: AuthUser | null;
  appState?: LearnerAppStateResponse | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onLogout: () => void;
  onTabChangeSpecial?: (tab: string) => void;
  children: React.ReactNode;
}

export function AppShell({
  user,
  appState,
  activeTab,
  setActiveTab,
  onLogout,
  onTabChangeSpecial,
  children,
}: AppShellProps) {
  const navTabs = [
    { id: "overview", label: "Overview" },
    { id: "goal", label: "My Goal" },
    { id: "diagnostic", label: "Diagnostic" },
    { id: "path", label: "Learning Path" },
    { id: "skills", label: "Skills" },
    { id: "progress", label: "Progress" },
    { id: "assistant", label: "AI Assistant" },
  ];

  function handleTabSelect(tabId: string) {
    setActiveTab(tabId);
    if (onTabChangeSpecial) onTabChangeSpecial(tabId);
  }

  return (
    <div className="min-h-screen bg-background text-primary flex flex-col font-sans transition-colors duration-200 relative overflow-x-hidden">
      <AmbientBackground />

      <Header
        user={user}
        activeTab={activeTab}
        navTabs={navTabs}
        onSelectTab={handleTabSelect}
        onLogout={onLogout}
      />

      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 py-6 md:py-10">
        {user && (
          <JourneyIndicator
            appState={appState || null}
            activeTab={activeTab}
            onNavigateTab={handleTabSelect}
          />
        )}
        {children}
      </main>

      <footer className="border-t border-subtle bg-surface/40 py-8 px-6 text-center text-xs text-muted">
        <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>Adaptive Learning Intelligence System © 2026</div>
          <div className="flex space-x-6 text-secondary font-medium">
            <span>Goal Intelligence</span>
            <span>Adaptive Diagnostic</span>
            <span>Dynamic Replanning</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
