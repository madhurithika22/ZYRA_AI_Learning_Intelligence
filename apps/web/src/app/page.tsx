"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth";
import { AppShell } from "../components/shell/AppShell";
import { AmbientBackground } from "../components/shell/AmbientBackground";
import {
  LandingHeader,
  LandingHero,
  ProductValues,
  HowItWorks,
  TrustSection,
  LandingCTA,
} from "../components/landing";
import { AuthForms } from "../components/AuthForms";
import { OnboardingView } from "../components/OnboardingView";
import { GoalSetupView } from "../components/GoalSetupView";
import { SelfAssessmentView } from "../components/SelfAssessmentView";
import { DiagnosticView } from "../components/DiagnosticView";
import { LearningTwinView } from "../components/LearningTwinView";
import { BottleneckView } from "../components/BottleneckView";
import { LearningPathView } from "../components/LearningPathView";
import { ActivityView } from "../components/ActivityView";
import { ProofView } from "../components/ProofView";
import { ProgressView } from "../components/ProgressView";
import { NextActionView } from "../components/NextActionView";
import { AssistantView } from "../components/AssistantView";
import { ReplanningView } from "../components/ReplanningView";
import { ProfileView } from "../components/ProfileView";
import { ErrorBoundary } from "../components/ErrorBoundary";

import {
  fetchLearnerAppState,
  fetchLearningTwin,
  fetchBottleneckAnalysis,
  generateLearningPaths,
} from "../lib/api";
import {
  AuthUser,
  LearnerAppStateResponse,
  LearningTwinResponse,
  BottleneckAnalysisResponse,
  PathComparisonResponse,
  PathNodeItem,
  getRouteForStage,
} from "../lib/types";

export default function Home() {
  const { user, status: authStatus, error: authError, checkAuth, setAuthUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<string>("landing");

  // Domain Data & App State
  const [appState, setAppState] = useState<LearnerAppStateResponse | null>(null);
  const [persistedGoalId, setPersistedGoalId] = useState<string | null>(null);
  const [twinData, setTwinData] = useState<LearningTwinResponse | null>(null);
  const [twinLoading, setTwinLoading] = useState<boolean>(false);
  const [twinError, setTwinError] = useState<string | null>(null);

  const [bottleneckData, setBottleneckData] = useState<BottleneckAnalysisResponse | null>(null);
  const [bottleneckLoading, setBottleneckLoading] = useState<boolean>(false);

  const [pathData, setPathData] = useState<PathComparisonResponse | null>(null);
  const [pathLoading, setPathLoading] = useState<boolean>(false);

  const [showReplanModal, setShowReplanModal] = useState<boolean>(false);
  const [activeAttemptId, setActiveAttemptId] = useState<string | null>(null);
  const [activePathNode, setActivePathNode] = useState<PathNodeItem | null>(null);

  async function refreshAppState() {
    const state = await fetchLearnerAppState();
    if (state) {
      setAppState(state);
      if (state.goal_id) setPersistedGoalId(state.goal_id);
    }
    return state;
  }

  async function loadLearnerState(learnerId: string) {
    setTwinLoading(true);
    setTwinError(null);
    try {
      const data = await fetchLearningTwin(learnerId);
      setTwinData(data);
      if (data?.goal?.goal_id) {
        setPersistedGoalId(data.goal.goal_id);
      }
      await refreshAppState();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load Learning Twin.";
      setTwinError(msg);
    } finally {
      setTwinLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;

    if (!user) return;

    fetchLearnerAppState().then((state) => {
      if (!isMounted) return;
      if (state) {
        setAppState(state);
        if (state.goal_id) setPersistedGoalId(state.goal_id);
        const resolvedRoute = getRouteForStage(state.stage);
        setActiveTab((prev) => {
          if (prev !== "landing" && prev !== "signin" && prev !== "signup") return prev;
          return resolvedRoute;
        });
      } else {
        setActiveTab((prev) => (prev === "landing" || prev === "signin" || prev === "signup" ? "overview" : prev));
      }
    });

    fetchLearningTwin(user.learner_id).then((data) => {
      if (!isMounted) return;
      setTwinData(data);
      if (data?.goal?.goal_id) {
        setPersistedGoalId(data.goal.goal_id);
      }
    }).catch((err: unknown) => {
      if (!isMounted) return;
      const msg = err instanceof Error ? err.message : "Failed to load Learning Twin.";
      setTwinError(msg);
    });

    return () => {
      isMounted = false;
    };
  }, [user]);

  // Compute effective tab to enforce Public vs Protected routing contract
  let effectiveTab = activeTab;
  if (!user) {
    // Unauthenticated visiting protected view -> redirect to Sign In
    if (activeTab !== "landing" && activeTab !== "signin" && activeTab !== "signup") {
      effectiveTab = "signin";
    }
  } else {
    // Authenticated visiting public view -> redirect to application stage route
    if (activeTab === "landing" || activeTab === "signin" || activeTab === "signup") {
      effectiveTab = getRouteForStage(appState?.stage);
    }
  }

  async function loadBottlenecks() {
    if (!user || !persistedGoalId) return;
    setBottleneckLoading(true);
    try {
      const data = await fetchBottleneckAnalysis(user.learner_id, persistedGoalId);
      setBottleneckData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setBottleneckLoading(false);
    }
  }

  async function loadPaths() {
    if (!user || !persistedGoalId) return;
    setPathLoading(true);
    try {
      const data = await generateLearningPaths(user.learner_id, persistedGoalId);
      setPathData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setPathLoading(false);
    }
  }

  async function handleLogout() {
    await logout();
    setTwinData(null);
    setBottleneckData(null);
    setPathData(null);
    setPersistedGoalId(null);
    setAppState(null);
    setActiveTab("landing");
  }

  function handleTabChangeSpecial(tab: string) {
    if (tab === "skills") loadBottlenecks();
    if (tab === "path") loadPaths();
    if (tab === "overview" && user) loadLearnerState(user.learner_id);
  }

  function handleAuthSuccess(authUser: AuthUser, nextTab?: string) {
    setAuthUser(authUser);
    if (nextTab) {
      setActiveTab(nextTab);
    } else {
      fetchLearnerAppState().then((state) => {
        if (state) {
          setAppState(state);
          setActiveTab(getRouteForStage(state.stage));
        } else {
          setActiveTab("overview");
        }
      });
    }
    loadLearnerState(authUser.learner_id);
  }

  if (authStatus === "loading") {
    return (
      <div className="min-h-screen bg-background text-primary flex items-center justify-center font-sans">
        <div className="flex items-center space-x-3 text-accent-primary">
          <div className="animate-spin h-6 w-6 border-2 border-current border-t-transparent rounded-full" />
          <span className="font-medium text-sm text-secondary">Checking session...</span>
        </div>
      </div>
    );
  }

  if (authStatus === "error") {
    return (
      <div className="min-h-screen bg-background text-primary flex items-center justify-center font-sans p-4">
        <div className="bg-surface border border-subtle rounded-3xl p-8 max-w-md w-full text-center space-y-6 shadow-lg">
          <div className="h-12 w-12 rounded-2xl bg-accent-rose/10 text-accent-rose flex items-center justify-center mx-auto">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-primary">Connection Error</h2>
            <p className="text-xs text-secondary leading-relaxed">
              {authError || "Unable to reach the authentication service. Please check your network connection and try again."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => checkAuth()}
            className="w-full py-3.5 rounded-2xl bg-accent-primary hover:opacity-90 text-white font-bold text-sm shadow-md transition-all"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // =========================================================================
  // Unauthenticated Visitor Flow (Landing, Sign In, Sign Up)
  // =========================================================================
  if (!user) {
    return (
      <div className="min-h-screen bg-background text-primary flex flex-col font-sans transition-colors duration-200 relative overflow-x-hidden">
        <AmbientBackground />

        <LandingHeader
          onSignIn={() => setActiveTab("signin")}
          onGetStarted={() => setActiveTab("signup")}
        />

        <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 py-6 md:py-10">
          <ErrorBoundary>
            {activeTab === "landing" && (
              <>
                <LandingHero
                  onStart={() => setActiveTab("signup")}
                  onLearnMore={() => {
                    const el = document.getElementById("how-it-works");
                    if (el) el.scrollIntoView({ behavior: "smooth" });
                  }}
                />
                <ProductValues />
                <HowItWorks />
                <TrustSection />
                <LandingCTA onStart={() => setActiveTab("signup")} />
              </>
            )}

            {activeTab === "signin" && (
              <div className="py-8 max-w-md mx-auto">
                <AuthForms
                  mode="signin"
                  onSuccess={(authUser, nextTab) => handleAuthSuccess(authUser, nextTab || "overview")}
                  onSwitchMode={() => setActiveTab("signup")}
                  onBackToLanding={() => setActiveTab("landing")}
                />
              </div>
            )}

            {activeTab === "signup" && (
              <div className="py-8 max-w-md mx-auto">
                <AuthForms
                  mode="signup"
                  onSuccess={(authUser) => handleAuthSuccess(authUser, "onboarding")}
                  onSwitchMode={() => setActiveTab("signin")}
                  onBackToLanding={() => setActiveTab("landing")}
                />
              </div>
            )}
          </ErrorBoundary>
        </main>

        <footer className="border-t border-subtle bg-surface/40 py-8 px-6 text-center text-xs text-muted">
          <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>Adaptive Learning Intelligence © 2026</div>
            <div className="flex space-x-6 text-secondary font-medium">
              <a href="#how-it-works" className="hover:text-primary transition-colors">How It Works</a>
              <a href="#why-adaptive" className="hover:text-primary transition-colors">Why Adaptive</a>
              <a href="#about-intelligence" className="hover:text-primary transition-colors">About</a>
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // =========================================================================
  // Authenticated Learner Dashboard Flow (AppShell with Full Navigation)
  // =========================================================================
  return (
    <AppShell
      user={user}
      appState={appState}
      activeTab={effectiveTab}
      setActiveTab={setActiveTab}
      onLogout={handleLogout}
      onTabChangeSpecial={handleTabChangeSpecial}
    >
      <ErrorBoundary>
        {/* Learner Onboarding Flow */}
        {activeTab === "onboarding" && (
          <OnboardingView
            user={user}
            onComplete={() => {
              refreshAppState();
              setActiveTab("goal");
            }}
          />
        )}

        {/* Goal Setup View */}
        {activeTab === "goal" && (
          <GoalSetupView
            user={user}
            onGoalSaved={(goalId) => {
              setPersistedGoalId(goalId);
              loadLearnerState(user.learner_id);
            }}
            onStartDiagnostic={(goalId) => {
              setPersistedGoalId(goalId);
              setActiveTab("selfassessment");
            }}
            onBackToProfile={() => setActiveTab("profile")}
          />
        )}

        {/* Self-Reported Baseline Assessment View */}
        {activeTab === "selfassessment" && (
          <SelfAssessmentView
            user={user}
            goalId={persistedGoalId}
            onComplete={() => {
              setActiveTab("diagnostic");
            }}
          />
        )}

        {/* Diagnostic Assessment View */}
        {activeTab === "diagnostic" && (
          <DiagnosticView
            user={user}
            goalId={persistedGoalId}
            onDiagnosticComplete={() => {
              loadLearnerState(user.learner_id);
              setActiveTab("overview");
            }}
            onNavigateToTab={(tab) => {
              setActiveTab(tab);
              handleTabChangeSpecial(tab);
            }}
            onBackToGoal={() => setActiveTab("goal")}
          />
        )}

        {/* Learning Twin Overview */}
        {activeTab === "overview" && (
          <LearningTwinView
            twinData={twinData}
            loading={twinLoading}
            error={twinError}
            onNavigateTab={(tab) => {
              setActiveTab(tab);
              handleTabChangeSpecial(tab);
            }}
          />
        )}

        {/* Skill Bottleneck Deep-Dive View */}
        {activeTab === "skills" && (
          <BottleneckView
            bottleneckData={bottleneckData}
            loading={bottleneckLoading}
            onRefresh={loadBottlenecks}
            onBackToOverview={() => setActiveTab("overview")}
            onNavigateToPath={() => setActiveTab("path")}
          />
        )}

        {/* Adaptive Learning Path View */}
        {activeTab === "path" && (
          <LearningPathView
            pathData={pathData}
            loading={pathLoading}
            onGenerate={loadPaths}
            onSelectNode={(nodeId) => {
              let foundNode = null;
              if (pathData?.options) {
                for (const opt of Object.values(pathData.options)) {
                  const match = opt.nodes?.find((n) => (n.id || n.node_id) === nodeId);
                  if (match) {
                    foundNode = match;
                    break;
                  }
                }
              }
              if (foundNode) setActivePathNode(foundNode);
              setActiveTab("activity");
            }}
            onBackToOverview={() => setActiveTab("overview")}
          />
        )}

        {/* Activity Attempt View */}
        {activeTab === "activity" && (
          <ActivityView
            user={user}
            pathNodeId={activePathNode?.id || activePathNode?.node_id}
            skillName={activePathNode?.skill_name || twinData?.bottleneck?.skill_name || "Target Skill"}
            activityTitle={activePathNode?.resource_title || "Hands-on Learning Activity"}
            estimatedMinutes={activePathNode?.estimated_minutes || 30}
            rationale={activePathNode?.rationale || "Targeted exercise designed to address your active bottleneck."}
            resourceUrl={activePathNode?.resource_url}
            onCompleteActivity={(attemptId) => {
              setActiveAttemptId(attemptId);
              setActiveTab("proof");
            }}
            onProveMastery={(attemptId) => {
              if (attemptId) setActiveAttemptId(attemptId);
              setActiveTab("proof");
            }}
            onBackToPath={() => setActiveTab("path")}
          />
        )}

        {/* Proof of Mastery View */}
        {activeTab === "proof" && (
          <ProofView
            user={user}
            activityAttemptId={activeAttemptId}
            pathNodeId={activePathNode?.id || activePathNode?.node_id}
            skillName={activePathNode?.skill_name || twinData?.bottleneck?.skill_name || twinData?.primary_bottleneck?.skill_name || "Docker"}
            onReturnOverview={() => {
              loadLearnerState(user.learner_id);
              setActiveTab("overview");
            }}
            onBackToActivity={() => setActiveTab("activity")}
          />
        )}

        {/* Progress View */}
        {activeTab === "progress" && (
          <ProgressView
            twinData={twinData}
            onBackToOverview={() => setActiveTab("overview")}
          />
        )}

        {/* Next Action View */}
        {activeTab === "nextaction" && (
          <NextActionView
            twinData={twinData}
            onExecuteAction={() => setActiveTab("activity")}
          />
        )}

        {/* Grounded AI Assistant View */}
        {activeTab === "assistant" && (
          <AssistantView
            user={user}
            appState={appState}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {/* Authenticated Profile View */}
        {activeTab === "profile" && (
          <ProfileView
            user={user}
            onLogout={handleLogout}
            onProfileUpdated={(updatedName) => {
              if (user) {
                setAuthUser({ ...user, display_name: updatedName });
              }
            }}
          />
        )}

        {/* Dynamic Replanning Diff Modal */}
        {showReplanModal && (
          <ReplanningView
            onClose={() => setShowReplanModal(false)}
            onAccept={() => {
              setShowReplanModal(false);
              loadLearnerState(user.learner_id);
            }}
          />
        )}
      </ErrorBoundary>
    </AppShell>
  );
}
