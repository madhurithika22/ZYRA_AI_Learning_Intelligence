"use client";

import React, { useState } from "react";
import { Button } from "./ui/Button";

interface ReplanningViewProps {
  onClose: () => void;
  onAccept: () => void;
}

export function ReplanningView({ onClose, onAccept }: ReplanningViewProps) {
  const [accepted, setAccepted] = useState(false);

  function handleConfirm() {
    setAccepted(true);
    setTimeout(() => {
      onAccept();
    }, 1000);
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-surface border border-subtle max-w-2xl w-full rounded-3xl p-8 md:p-10 shadow-2xl space-y-8 animate-in fade-in zoom-in-95 duration-200">
        <div className="space-y-2 border-b border-subtle pb-6">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-primary">
            Dynamic Replanning Engine
          </span>
          <h2 className="text-2xl md:text-3xl font-extrabold text-primary tracking-tight">
            YOUR PATH HAS CHANGED
          </h2>
          <div className="flex items-center space-x-3 text-xs font-bold text-secondary pt-1">
            <span>Version 1</span>
            <span>→</span>
            <span className="text-accent-primary font-extrabold">Version 2 (Draft)</span>
          </div>
        </div>

        {/* Visual Diff Section */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
            Path Version Diff
          </h3>

          <div className="space-y-3">
            {/* KEEP */}
            <div className="bg-subtle/50 border border-subtle p-4 rounded-2xl flex items-center justify-between text-xs">
              <span className="font-bold text-primary">KEEP: Completed Work & Core ML Prerequisites</span>
              <span className="px-2.5 py-1 bg-subtle text-secondary rounded-full font-semibold">
                3 Nodes
              </span>
            </div>

            {/* REMOVE */}
            <div className="bg-accent-rose-subtle border border-accent-rose/30 p-4 rounded-2xl flex items-center justify-between text-xs">
              <span className="font-bold text-accent-rose">REMOVE: Redundant Introductory Modules</span>
              <span className="px-2.5 py-1 bg-accent-rose-subtle text-accent-rose rounded-full font-semibold">
                -1 Node
              </span>
            </div>

            {/* ADD */}
            <div className="bg-accent-mint-subtle border border-accent-mint/30 p-4 rounded-2xl flex items-center justify-between text-xs">
              <span className="font-bold text-accent-mint">
                ADD: Targeted Docker & Model Deployment Intervention
              </span>
              <span className="px-2.5 py-1 bg-accent-mint-subtle text-accent-mint rounded-full font-semibold">
                +1 Node
              </span>
            </div>
          </div>
        </div>

        {accepted && (
          <div className="bg-accent-mint-subtle border border-accent-mint/30 rounded-2xl p-4 text-xs font-bold text-accent-mint text-center">
            ✓ Path Version 2 accepted and activated!
          </div>
        )}

        <div className="flex items-center justify-end space-x-4 pt-2">
          <Button variant="secondary" size="md" onClick={onClose}>
            Keep Current Path
          </Button>
          <Button variant="primary" size="md" onClick={handleConfirm}>
            Accept Path Update →
          </Button>
        </div>
      </div>
    </div>
  );
}
