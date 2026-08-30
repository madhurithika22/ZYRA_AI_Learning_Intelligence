"use client";

import React, { useState } from "react";
import { ThemeToggle } from "../shell/ThemeToggle";
import { Button } from "../ui/Button";

interface LandingHeaderProps {
  onSignIn: () => void;
  onGetStarted: () => void;
}

export function LandingHeader({ onSignIn, onGetStarted }: LandingHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function scrollToSection(id: string) {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-subtle bg-surface/85 backdrop-blur-md px-4 sm:px-6 lg:px-8 py-3.5 transition-colors">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between gap-4">
        {/* Brand Left */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => {
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="flex items-center gap-3 group text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-xl"
            aria-label="ZYRA Home"
          >
            <div className="h-9 w-9 rounded-xl bg-accent-primary flex items-center justify-center text-white font-extrabold text-sm shadow-xs group-hover:opacity-90 transition-all">
              Z
            </div>
            <span className="font-bold text-base sm:text-lg tracking-tight text-primary">
              ZYRA
            </span>
          </button>
        </div>

        {/* Unauthenticated Nav Links Center/Right (Desktop 768px+) */}
        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-secondary" aria-label="Landing page menu">
          <button
            type="button"
            onClick={() => scrollToSection("how-it-works")}
            className="hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-lg px-2 py-1"
          >
            How It Works
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("why-adaptive")}
            className="hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-lg px-2 py-1"
          >
            Why Adaptive
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("about-intelligence")}
            className="hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary rounded-lg px-2 py-1"
          >
            About
          </button>
        </nav>

        {/* Auth & Theme Actions Right */}
        <div className="flex items-center gap-3 shrink-0">
          <ThemeToggle />

          <div className="hidden sm:flex items-center gap-2.5">
            <Button variant="ghost" size="sm" onClick={onSignIn}>
              Sign In
            </Button>
            <Button variant="primary" size="sm" onClick={onGetStarted}>
              Get Started
            </Button>
          </div>

          {/* Mobile Hamburger Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label="Toggle Navigation Menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="landing-mobile-menu"
            className="md:hidden p-2 rounded-xl bg-surface border border-subtle text-secondary hover:text-primary hover:bg-subtle transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
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
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div id="landing-mobile-menu" className="md:hidden border-t border-subtle mt-3 pt-4 pb-3 space-y-3 bg-surface/95 backdrop-blur-md rounded-2xl px-4 shadow-lg">
          <nav className="flex flex-col space-y-2 text-sm font-medium text-secondary">
            <button
              type="button"
              onClick={() => scrollToSection("how-it-works")}
              className="text-left px-3 py-2 rounded-lg hover:bg-subtle hover:text-primary transition-all"
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("why-adaptive")}
              className="text-left px-3 py-2 rounded-lg hover:bg-subtle hover:text-primary transition-all"
            >
              Why Adaptive
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("about-intelligence")}
              className="text-left px-3 py-2 rounded-lg hover:bg-subtle hover:text-primary transition-all"
            >
              About
            </button>
          </nav>
          <div className="pt-3 border-t border-subtle flex flex-col gap-2">
            <Button variant="ghost" className="w-full justify-center" onClick={() => { setMobileMenuOpen(false); onSignIn(); }}>
              Sign In
            </Button>
            <Button variant="primary" className="w-full justify-center" onClick={() => { setMobileMenuOpen(false); onGetStarted(); }}>
              Get Started
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}

