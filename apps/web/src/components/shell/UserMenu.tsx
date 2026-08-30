"use client";

import React, { useState, useRef, useEffect } from "react";
import { AuthUser } from "../../lib/types";
import { LearnerAvatar } from "../identity/LearnerAvatar";

export interface UserMenuProps {
  user: AuthUser;
  onNavigateProfile: () => void;
  onLogout: () => void;
}

export function UserMenu({ user, onNavigateProfile, onLogout }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const displayName = user.display_name || "Learner";
  const email = user.email || "";

  function navigateTo(hash?: string) {
    setIsOpen(false);
    onNavigateProfile();
    if (hash) {
      setTimeout(() => {
        window.location.hash = hash;
        const elem = document.getElementById(hash);
        if (elem) {
          elem.scrollIntoView({ behavior: "smooth" });
        }
      }, 50);
    }
  }

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label="User Account Menu"
        className="flex items-center gap-2.5 p-1 rounded-2xl hover:bg-subtle/60 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
      >
        <LearnerAvatar displayName={displayName} size="sm" showBadge />
        <div className="text-left hidden sm:block">
          <div className="text-xs font-bold text-primary truncate max-w-[120px]">
            {displayName}
          </div>
          <div className="text-[11px] text-muted truncate max-w-[140px]">{email}</div>
        </div>
        <svg
          className={`w-4 h-4 text-muted transition-transform duration-180 ${
            isOpen ? "rotate-180 text-primary" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 mt-2 w-60 bg-surface border border-subtle rounded-2xl shadow-lg py-2 z-50 animate-in fade-in duration-150"
        >
          <div className="px-4 py-2.5 border-b border-subtle">
            <div className="text-xs font-bold text-primary">{displayName}</div>
            <div className="text-[11px] text-muted truncate">{email}</div>
          </div>

          <div className="py-1">
            <button
              role="menuitem"
              onClick={() => navigateTo()}
              className="w-full text-left px-4 py-2.5 text-xs font-semibold text-secondary hover:text-primary hover:bg-subtle/50 flex items-center gap-2.5 transition-all"
            >
              <svg className="w-4 h-4 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>Profile</span>
            </button>

            <button
              role="menuitem"
              onClick={() => navigateTo("achievements")}
              className="w-full text-left px-4 py-2.5 text-xs font-semibold text-secondary hover:text-primary hover:bg-subtle/50 flex items-center gap-2.5 transition-all"
            >
              <svg className="w-4 h-4 text-accent-amber" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4m6 0.01A9 9 0 1112 3v.01M16 11l-4 4-2-2" />
              </svg>
              <span>Achievements</span>
            </button>

            <button
              role="menuitem"
              onClick={() => navigateTo("preferences")}
              className="w-full text-left px-4 py-2.5 text-xs font-semibold text-secondary hover:text-primary hover:bg-subtle/50 flex items-center gap-2.5 transition-all"
            >
              <svg className="w-4 h-4 text-accent-sky" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              <span>Learning Preferences</span>
            </button>
          </div>

          <div className="border-t border-subtle pt-1 mt-1">
            <button
              role="menuitem"
              onClick={() => {
                setIsOpen(false);
                onLogout();
              }}
              className="w-full text-left px-4 py-2.5 text-xs font-semibold text-accent-rose hover:bg-accent-rose-subtle flex items-center gap-2.5 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Log Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
