"use client";

import React from "react";
import { IconButton } from "./IconButton";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  size?: "sm" | "md" | "lg" | "xl";
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  size = "md",
  children,
  footer,
  className = "",
}: ModalProps) {
  React.useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeStyles = {
    sm: "max-w-sm",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
  }[size];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className={`w-full bg-surface border border-subtle rounded-3xl shadow-xl overflow-hidden transition-all duration-200 transform scale-100 ${sizeStyles} ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || subtitle) && (
          <div className="px-6 py-5 border-b border-subtle flex items-start justify-between gap-4">
            <div className="space-y-1">
              {title && <h2 className="text-h2 font-bold text-primary">{title}</h2>}
              {subtitle && <p className="text-body-sm text-secondary">{subtitle}</p>}
            </div>
            <IconButton
              aria-label="Close modal"
              variant="ghost"
              size="sm"
              onClick={onClose}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              }
            />
          </div>
        )}

        {/* Body Content */}
        <div className="p-6 overflow-y-auto max-h-[75vh] space-y-4">{children}</div>

        {/* Footer Actions */}
        {footer && (
          <div className="px-6 py-4 border-t border-subtle bg-subtle/30 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
