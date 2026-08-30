"use client";

import React, { useState } from "react";
import { AuthUser } from "../../lib/types";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";
import { Navigation, NavTabItem } from "./Navigation";
import { MobileNavigation } from "./MobileNavigation";
import { Button } from "../ui/Button";

export interface HeaderProps {
  user: AuthUser | null;
  activeTab: string;
  navTabs: NavTabItem[];
  onSelectTab: (tabId: string) => void;
  onLogout: () => void;
}

export function Header({
  user,
  activeTab,
  navTabs,
  onSelectTab,
  onLogout,
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function handleTabClick(id: string) {
    onSelectTab(id);
    setMobileMenuOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-subtle bg-surface/85 backdrop-blur-md px-4 sm:px-6 lg:px-8 py-3.5 transition-colors">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between gap-4">
        {/* Brand Left */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => handleTabClick(user ? "overview" : "landing")}
            className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-xl"
            aria-label="Adaptive Learning Intelligence Home"
          >
            <div className="h-9 w-9 rounded-xl bg-accent-primary flex items-center justify-center text-white font-extrabold text-sm shadow-xs group-hover:opacity-90 transition-all">
              A
            </div>
            <span className="font-bold text-base sm:text-lg tracking-tight text-primary">
              Adaptive Learning Intelligence
            </span>
          </button>
        </div>

        {/* Navigation Center (Desktop 1024px+) */}
        {user && (
          <Navigation
            navTabs={navTabs}
            activeTab={activeTab}
            onSelectTab={handleTabClick}
          />
        )}

        {/* Learner Identity Right */}
        <div className="flex items-center gap-3 shrink-0">
          <ThemeToggle />

          {user ? (
            <div className="flex items-center gap-2">
              <UserMenu
                user={user}
                onNavigateProfile={() => handleTabClick("profile")}
                onLogout={onLogout}
              />

              {/* Mobile Menu Hamburger Toggle */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen((prev) => !prev)}
                aria-label="Toggle Mobile Navigation Menu"
                aria-expanded={mobileMenuOpen}
                className="lg:hidden p-2.5 rounded-xl bg-surface border border-subtle text-secondary hover:text-primary hover:bg-subtle transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <Button variant="ghost" size="sm" onClick={() => handleTabClick("signin")}>
                Sign In
              </Button>
              <Button variant="primary" size="sm" onClick={() => handleTabClick("signup")}>
                Get Started
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {user && (
        <MobileNavigation
          navTabs={navTabs}
          activeTab={activeTab}
          isOpen={mobileMenuOpen}
          onSelectTab={handleTabClick}
        />
      )}
    </header>
  );
}
