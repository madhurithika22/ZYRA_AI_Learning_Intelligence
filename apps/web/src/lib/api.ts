import {
  ActivityAttemptResponse,
  AuthUser,
  BottleneckAnalysisResponse,
  DiagnosticQuestion,
  GoalCreationResponse,
  GoalIntelligenceResult,
  LearnerAppStateResponse,
  LearnerProfileData,
  LearningTwinResponse,
  PathComparisonResponse,
  ProofOfMasteryOutcomeResponse,
  SourceReference,
  StartMasteryCheckResponse,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://zyra-ai-learning-intelligence.onrender.com";

// --- NEW AUTHENTICATED FETCH WRAPPER ---
async function fetchWithAuth(url: string | URL, options: RequestInit = {}): Promise<Response> {
  let token: string | null = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("session_token");
  }

  const headers = new Headers(options.headers || {});
  
  // Attach the Bearer token if it exists
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, {
    ...options,
    headers,
  });
}
// ---------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let errorMsg = `HTTP error ${res.status}`;
    if (typeof data?.detail === "string") {
      errorMsg = data.detail;
    } else if (Array.isArray(data?.detail)) {
      errorMsg = data.detail
        .map((item: unknown) => {
          if (typeof item === "string") return item;
          if (typeof item === "object" && item !== null) {
            const errObj = item as Record<string, unknown>;
            const locArr = Array.isArray(errObj.loc) ? errObj.loc.join(".") + ": " : "";
            const msgStr = typeof errObj.msg === "string" ? errObj.msg : JSON.stringify(item);
            return locArr + msgStr;
          }
          return String(item);
        })
        .join("; ");
    } else if (typeof data?.detail === "object" && data?.detail !== null) {
      errorMsg = data.detail.message || data.detail.error || JSON.stringify(data.detail);
    } else if (typeof data?.message === "string") {
      errorMsg = data.message;
    }
    throw new Error(errorMsg);
  }
  return data as T;
}

export async function fetchCurrentAuthUser(): Promise<AuthUser | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/auth/me`);
    if (res.status === 401) return null;
    return await handleResponse<AuthUser>(res);
  } catch {
    return null;
  }
}

export async function fetchLearnerAppState(): Promise<LearnerAppStateResponse | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/me/state`);
    if (res.status === 401) return null;
    return await handleResponse<LearnerAppStateResponse>(res);
  } catch {
    return null;
  }
}

export async function loginUser(email: string, password: string): Promise<AuthUser> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await handleResponse<AuthUser & { access_token?: string }>(res);
  if (data.access_token && typeof window !== "undefined") {
    localStorage.setItem("session_token", data.access_token);
  }
  return data;
}

export async function registerUser(
  displayName: string,
  email: string,
  password: string
): Promise<AuthUser> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      display_name: displayName,
      email,
      password,
    }),
  });
  
  const data = await handleResponse<AuthUser & { access_token?: string }>(res);
  if (data.access_token && typeof window !== "undefined") {
    localStorage.setItem("session_token", data.access_token);
  }
  return data;
}

export async function logoutUser(): Promise<void> {
  await fetchWithAuth(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
  });
}

export async function interpretGoal(
  naturalLanguageGoal: string
): Promise<GoalIntelligenceResult> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/goal-intelligence/interpret`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ natural_language_goal: naturalLanguageGoal }),
  });
  return handleResponse<GoalIntelligenceResult>(res);
}

export async function saveGoal(
  learnerId: string,
  naturalLanguageGoal: string
): Promise<GoalCreationResponse> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ natural_language_goal: naturalLanguageGoal }),
  });
  return handleResponse<GoalCreationResponse>(res);
}

export async function fetchLatestDiagnosticSession(
  learnerId: string,
  goalId: string
): Promise<{ session_id: string; status: string; question_count: number; max_questions: number } | null> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/learners/${learnerId}/diagnostics/latest?goal_id=${goalId}`
  );
  if (res.status === 404 || res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok || !data) return null;
  return {
    session_id: data.session_id || data.id,
    status: data.status,
    question_count: data.question_count || 0,
    max_questions: data.max_questions || 10,
  };
}

export async function fetchLearnerSkillState(
  learnerId: string,
  goalId: string
): Promise<{ learner_id: string; goal_id: string; target_role: string; skills: Array<{ skill_id: string; skill_name: string; required_level: number; role_importance: number; mastery_score: number; confidence: number; evidence_count: number }> } | null> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/learners/${learnerId}/skill-state?goal_id=${goalId}`
  );
  if (res.status === 404) return null;
  return handleResponse(res);
}

export async function startDiagnosticSession(
  learnerId: string,
  goalId: string,
  forceNew: boolean = false
): Promise<{ session_id: string }> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/diagnostics?learner_id=${learnerId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal_id: goalId, max_questions: 10, force_new: forceNew }),
  });
  const data = await handleResponse<{ id?: string; session_id?: string }>(res);
  return { session_id: data.session_id || data.id || "" };
}

export async function getNextQuestion(
  sessionId: string
): Promise<DiagnosticQuestion | null> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/diagnostics/${sessionId}/next-question`, {
    method: "POST",
  });
  if (res.status === 204) return null;
  return handleResponse<DiagnosticQuestion>(res);
}

export async function submitDiagnosticAnswer(
  sessionId: string,
  questionId: string,
  selectedOption: string
): Promise<{ demonstrated_score: number; evaluation_feedback: string; updated_mastery: number; is_session_completed?: boolean }> {
  const idempotencyKey = `diag-${sessionId}-${questionId}-${Date.now()}`;
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/diagnostics/${sessionId}/responses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idempotency_key: idempotencyKey,
      question_id: questionId,
      learner_answer: selectedOption,
    }),
  });
  const data = await handleResponse<{
    score?: number;
    demonstrated_score?: number;
    evaluation_summary?: string;
    evaluation_feedback?: string;
    is_session_completed?: boolean;
  }>(res);
  return {
    demonstrated_score: data.score ?? data.demonstrated_score ?? 1.0,
    evaluation_feedback: data.evaluation_summary || data.evaluation_feedback || "Response evaluated.",
    updated_mastery: data.score ?? 1.0,
    is_session_completed: data.is_session_completed,
  };
}

export async function submitSelfAssessment(
  sessionId: string,
  ratings: Record<string, string>
): Promise<void> {
  await fetchWithAuth(`${API_BASE_URL}/api/v1/diagnostics/${sessionId}/self-assessment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ratings }),
  });
}

export async function fetchDiagnosticHistory(
  learnerId: string,
  goalId: string
): Promise<{ history: Array<{ session_id: string; started_at: string; completed_at?: string | null; status: string; question_count: number; skills_count: number; termination_reason?: string | null }> }> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/diagnostics/history?goal_id=${goalId}`);
  if (res.status === 404) return { history: [] };
  return handleResponse(res);
}

export async function fetchLearningTwin(
  learnerId: string
): Promise<LearningTwinResponse | null> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/learning-twin`);
  if (res.status === 404) return null;
  return handleResponse<LearningTwinResponse>(res);
}

export async function fetchBottleneckAnalysis(
  learnerId: string,
  goalId: string
): Promise<BottleneckAnalysisResponse> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/learners/${learnerId}/goals/${goalId}/bottlenecks`
  );
  return handleResponse<BottleneckAnalysisResponse>(res);
}

export async function generateLearningPaths(
  learnerId: string,
  goalId: string
): Promise<PathComparisonResponse> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/learners/${learnerId}/goals/${goalId}/paths/generate`,
    { method: "POST" }
  );
  return handleResponse<PathComparisonResponse>(res);
}

export async function sendChatMessage(
  learnerId: string,
  sessionId: string | null,
  message: string
): Promise<{
  message_id: string;
  content: string;
  sources?: SourceReference[];
  response_type?: string;
  suggested_followups?: string[];
  session_id: string;
}> {
  let activeSessionId = sessionId;
  if (!activeSessionId) {
    const sessRes = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/conversation/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ learner_id: learnerId, title: "Learning Assistant Query" }),
    });
    const sessData = await handleResponse<{ id?: string; session_id?: string }>(sessRes);
    activeSessionId = sessData.id || sessData.session_id || "";
  }

  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/conversation/sessions/${activeSessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, message }),
  });
  const data = await handleResponse<{
    id?: string;
    message_id?: string;
    content: string;
    sources?: SourceReference[];
    response_type?: string;
    suggested_followups?: string[];
  }>(res);

  return {
    message_id: data.id || data.message_id || "",
    content: typeof data.content === "string" ? data.content : JSON.stringify(data.content),
    sources: data.sources || [],
    response_type: data.response_type,
    suggested_followups: data.suggested_followups || [],
    session_id: activeSessionId,
  };
}

export async function fetchLearnerProfile(learnerId: string): Promise<LearnerProfileData> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/profile`);
  return handleResponse<LearnerProfileData>(res);
}

export async function updateLearnerProfile(
  learnerId: string,
  payload: {
    display_name?: string;
    experience_level?: string;
    preferred_learning_mode?: string;
    weekly_availability_hours?: number;
    stated_background?: string;
    gender?: string;
    avatar_gender?: string;
    avatar_variant?: string;
  }
): Promise<LearnerProfileData> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learners/${learnerId}/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<LearnerProfileData>(res);
}

export async function fetchActiveMasteryCheck(
  activityAttemptId: string,
  learnerId: string
): Promise<StartMasteryCheckResponse | null> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/mastery-checks/active?activity_attempt_id=${activityAttemptId}&learner_id=${learnerId}`
  );
  if (res.status === 404 || res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok || !data) return null;
  return data as StartMasteryCheckResponse;
}

export async function startMasteryCheck(
  activityAttemptId: string,
  learnerId: string
): Promise<StartMasteryCheckResponse> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/v1/mastery-checks/${activityAttemptId}/start?learner_id=${learnerId}`,
    {
      method: "POST",
    }
  );
  return handleResponse<StartMasteryCheckResponse>(res);
}

export async function submitMasteryCheck(
  checkId: string,
  learnerId: string,
  answers: Array<{ question_id: string; learner_answer: string }>
): Promise<ProofOfMasteryOutcomeResponse> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/mastery-checks/${checkId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, answers }),
  });
  return handleResponse<ProofOfMasteryOutcomeResponse>(res);
}

export async function startLearningActivity(
  pathNodeId: string,
  learnerId: string
): Promise<ActivityAttemptResponse> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learning-activities/${pathNodeId}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId }),
  });
  return handleResponse<ActivityAttemptResponse>(res);
}

export async function completeLearningActivity(
  attemptId: string,
  learnerId: string,
  submissionData?: Record<string, unknown>
): Promise<ActivityAttemptResponse> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learning-activities/${attemptId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, completion_percentage: 100.0, submission_data: submissionData }),
  });
  return handleResponse<ActivityAttemptResponse>(res);
}

export async function saveActivityDraft(
  attemptId: string,
  learnerId: string,
  submissionData: Record<string, unknown>
): Promise<ActivityAttemptResponse> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learning-activities/${attemptId}/save-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, submission_data: submissionData }),
  });
  return handleResponse<ActivityAttemptResponse>(res);
}

export async function fetchLatestActivityAttempt(
  learnerId: string,
  nodeId?: string
): Promise<ActivityAttemptResponse | null> {
  const url = new URL(`${API_BASE_URL}/api/v1/learning-activities/latest-attempt`);
  url.searchParams.append("learner_id", learnerId);
  if (nodeId) url.searchParams.append("node_id", nodeId);

  const res = await fetchWithAuth(url.toString(), {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<ActivityAttemptResponse | null>(res);
}

export async function fetchActiveActivityAttempt(): Promise<{
  attempt: ActivityAttemptResponse | null;
  node_id: string | null;
  skill_name?: string;
  resource_title?: string;
}> {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/v1/learning-activities/active-attempt`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<{
    attempt: ActivityAttemptResponse | null;
    node_id: string | null;
    skill_name?: string;
    resource_title?: string;
  }>(res);
}
