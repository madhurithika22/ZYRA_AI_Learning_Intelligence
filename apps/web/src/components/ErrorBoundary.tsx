"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Unhandled UI error caught by ErrorBoundary:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-2xl mx-auto py-16 px-6 text-center space-y-6">
          <div className="bg-surface border border-subtle rounded-3xl p-8 md:p-12 shadow-xs space-y-6">
            <div className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-rose-500">
                Application Rendering Notice
              </span>
              <h2 className="text-2xl font-extrabold text-primary">
                Something went wrong loading this section
              </h2>
              <p className="text-xs text-secondary max-w-md mx-auto leading-relaxed">
                An unexpected interface error occurred. Click retry below to reload your learning state safely.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-subtle/50 border border-subtle p-4 rounded-2xl text-left font-mono text-[11px] text-secondary overflow-x-auto">
                {this.state.error.message}
              </div>
            )}

            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl text-xs shadow-xs transition-all"
            >
              Retry / Reload Section →
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
