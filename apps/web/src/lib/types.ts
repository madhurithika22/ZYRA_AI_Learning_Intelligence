export interface AuthUser {
  user_id: string;
  learner_id: string;
  email: string;
  display_name: string;
  access_token?: string;
  token_type?: string;
}

export interface LearnerAppStateResponse {
  learner_id: string;
  stage:
    | "GOAL_REQUIRED"
    | "DIAGNOSTIC_REQUIRED"
    | "DIAGNOSTIC_IN_PROGRESS"
    | "PATH_SELECTION"
    | "ACTIVE_LEARNING"
    | "PROOF_REQUIRED"
    | "ADAPTIVE_CONTINUATION";
  next_action_label: string;
  next_action_route: string;
  goal_id: string | null;
  target_role: string | null;
  active_path_id: string | null;
  primary_bottleneck_skill: string | null;
  progress_pct: number;
  state_confidence: string;
  diagnostic_session_id: string | null;
}

export interface ResolvedSkillItem {
  skill_id: string;
  name: string;
}

export interface GoalInterpretation {
  target_role: string;
  objective: string;
  timeline_weeks: number | null;
  daily_minutes: number | null;
  desired_outcome: string | null;
  constraints: string[];
  stated_existing_skills: string[];
  ambiguities: string[];
  confidence: number;
}

export interface ResolvedRoleInfo {
  canonical_role_id: string | null;
  canonical_role_name: string | null;
  confidence: number;
  is_resolved: boolean;
  ambiguity_reason: string | null;
}

export interface ResolvedSkillInfo {
  resolved_skills: ResolvedSkillItem[];
  unresolved_skills: string[];
}

export interface GoalIntelligenceResult {
  interpretation: GoalInterpretation;
  resolved_role: ResolvedRoleInfo;
  resolved_skills: ResolvedSkillInfo;
  validation_status: string;
  is_valid: boolean;
  validation_errors: string[];
}

export interface GoalCreationResponse {
  goal_id: string;
  learner_id: string;
  target_role_id: string;
  objective: string;
  timeline_weeks: number | null;
  daily_minutes: number | null;
  intelligence_result: GoalIntelligenceResult;
}

export interface DiagnosticQuestion {
  session_id: string;
  question_id: string;
  skill_id: string;
  skill_name: string;
  question_type: string;
  difficulty: number;
  prompt: string;
  options: string[] | null;
  question_number: number;
  total_questions: number;
}

export interface DiagnosticHistoryItem {
  session_id: string;
  started_at: string;
  completed_at?: string | null;
  status: string;
  question_count: number;
  skills_count: number;
  termination_reason?: string | null;
}

export interface DiagnosticHistoryResponse {
  learner_id: string;
  goal_id: string;
  history: DiagnosticHistoryItem[];
}

export interface LearnerSkillStateItem {
  skill_id: string;
  skill_name: string;
  required_level: number;
  role_importance: number;
  mastery_score: number;
  confidence: number;
  evidence_count: number;
  last_assessed_at: string | null;
}

export interface BottleneckExplanation {
  primary_reason: string;
  evidence: string[];
  downstream_skills: string[];
}

export interface SkillGapItem {
  skill_id: string;
  skill_name: string;
  required_level: number;
  mastery: number;
  confidence: number;
  gap: number;
  role_importance: number;
  dependency_impact: number;
  uncertainty_factor: number;
  bottleneck_score: number;
  rank: number;
  classification: string;
  explanation: BottleneckExplanation;
}

export interface BottleneckAnalysisResponse {
  learner_id: string;
  goal_id: string;
  target_role: string;
  analyzed_at: string;
  primary_bottleneck: SkillGapItem | null;
  all_gaps: SkillGapItem[];
}

export interface PathNodeItem {
  node_id?: string;
  id?: string;
  skill_id?: string;
  skill_name?: string;
  resource_id?: string;
  resource_title?: string;
  resource_type?: string;
  resource_url?: string | null;
  sequence_index?: number;
  estimated_minutes: number;
  status?: string;
  is_bottleneck?: boolean;
  activity_type?: string;
  rationale?: string;
}

export interface PathStrategyOption {
  strategy_name?: string;
  name?: string;
  path_id: string;
  description?: string;
  explanation?: string;
  estimated_days?: number;
  estimated_weeks?: number;
  total_minutes?: number;
  estimated_minutes?: number;
  node_count?: number;
  target_role_coverage?: number;
  target_skill_coverage?: number;
  is_active?: boolean;
  nodes: PathNodeItem[];
}

export interface PathComparisonResponse {
  learner_id: string;
  goal_id: string;
  generated_at: string;
  options: Record<string, PathStrategyOption>;
}

export interface ProgressSummary {
  weighted_goal_progress: number;
  target_role_skill_progress: number;
  total_activities_completed: number;
  mastery_checks_passed: number;
  path_nodes_completed: number;
  total_path_nodes: number;
}

export interface TwinGoalSummary {
  goal_id?: string | null;
  objective: string;
  target_role_id?: string | null;
  target_role_name: string;
  goal_skill_progress: number;
  target_skill_count: number;
  skills_at_required: number;
  skills_near_target: number;
  skills_needing_work: number;
  skills_uncertain: number;
  evidence_count: number;
}

export interface TwinSkillItem {
  skill_id: string;
  skill_name: string;
  mastery: number;
  confidence: number;
  required: number;
  gap: number;
  progress_to_required: number;
  evidence_count: number;
  status: string;
  // Aliases for component compatibility
  mastery_score?: number;
  role_importance?: number;
}

export interface TwinBottleneckSummary {
  skill_id?: string | null;
  skill_name: string;
  mastery_score?: number;
  required_level?: number;
  gap?: number;
  confidence?: number;
  dependency_impact?: number;
  bottleneck_score?: number;
  reason: string;
  affected_skills?: string[];
  explanation?: { primary_reason?: string };
}

export interface TwinNextActionSummary {
  action_type: string;
  title: string;
  target_skill_id?: string | null;
  target_skill_name: string;
  skill_name?: string;
  resource_id?: string | null;
  node_id?: string | null;
  estimated_minutes: number;
  action_confidence?: number;
  score?: number;
  primary_reason: string;
  rationale?: string;
  reasons?: string[];
}

export interface TwinPathSummary {
  path_id?: string | null;
  version: number;
  name: string;
  status: string;
  completion_percentage: number;
  completed_nodes: number;
  total_nodes: number;
  remaining_minutes: number;
  is_stale: boolean;
  replan_available: boolean;
}

export interface TwinFreshness {
  status: string;
  generated_at: string;
  latest_mastery_update_at?: string | null;
  latest_path_change_at?: string | null;
}

export interface TwinStateConfidence {
  level: string;
  score: number;
  reason: string;
  missing_dimensions?: string[];
}

export interface TwinEvidenceSummary {
  total_evidence_count: number;
  recent_evidence_count: number;
  last_assessed_at?: string | null;
  demonstrated_skills_count: number;
  improving_skills_count: number;
  insufficient_evidence_count: number;
  recently_verified_skills?: string[];
}

export interface LearningTwinResponse {
  learner_id: string;
  display_name: string;
  goal: TwinGoalSummary;
  path?: TwinPathSummary | null;
  skills: TwinSkillItem[];
  bottleneck?: TwinBottleneckSummary | null;
  next_action?: TwinNextActionSummary | null;
  replan?: Record<string, unknown> | null;
  recent_changes?: Array<{ id: string; title: string; change_type: string; description: string; timestamp: string; impact_delta?: string | null }>;
  evidence_summary: TwinEvidenceSummary;
  state_confidence: TwinStateConfidence;
  state_completeness: number;
  freshness: TwinFreshness;
  decision_trace?: Record<string, unknown> | null;

  // Aliases for backwards compatibility in components
  goal_skills?: TwinSkillItem[];
  primary_bottleneck?: TwinBottleneckSummary | null;
  next_best_action?: TwinNextActionSummary | null;
  overall_progress?: { weighted_goal_progress: number };
}

export interface SourceReference {
  source_type: string;
  source_id: string;
  label: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  citations?: string[];
  suggestedFollowups?: string[];
  responseType?: string;
  timestamp: string;
}

export interface AchievementBadgeItem {
  id: string;
  title: string;
  description: string;
  condition: string;
  unlocked: boolean;
  unlocked_at?: string | null;
  earned_at?: string | null;
  icon: string;
}

export interface WeeklyActivityDayItem {
  day: string;
  date: string;
  active: boolean;
  is_today: boolean;
}

export interface LearningIdentitySummaryItem {
  target_role?: string | null;
  strongest_skill?: string | null;
  biggest_opportunity?: string | null;
  consistency_text: string;
  evidence_text: string;
}

export interface LearnerGamificationStatsItem {
  streak_days: number;
  current_streak: number;
  longest_streak: number;
  xp: number;
  level: number;
  achievement_tier: string;
  current_level_base_xp: number;
  next_level_xp: number;
  xp_remaining: number;
  level_progress_pct: number;
  evidence_count: number;
  weekly_activity_strip?: WeeklyActivityDayItem[];
  weekly_active_days_count?: number;
  today_active?: boolean;
  strengths?: string[];
  growth_areas?: string[];
  identity_summary?: LearningIdentitySummaryItem;
  achievements: AchievementBadgeItem[];
}

export interface LearnerGoalProgressSummaryItem {
  goal_id?: string | null;
  target_role?: string | null;
  progress_percentage: number;
}

export interface LearnerProfileData {
  learner_id: string;
  display_name: string;
  email: string;
  profile?: {
    experience_level?: string;
    preferred_learning_mode?: string;
    weekly_availability_hours?: number;
    stated_background?: string;
    gender?: string | null;
    avatar_gender?: string | null;
    avatar_variant?: string | null;
    profile_metadata?: Record<string, unknown>;
  };
  gamification?: LearnerGamificationStatsItem;
  current_journey?: LearnerGoalProgressSummaryItem | null;
  goals_count?: number;
  goals?: Array<{
    id: string;
    target_role_id?: string;
    natural_language_goal?: string;
    status?: string;
  }>;
}

export interface MasteryCheckQuestionItem {
  question_id: string;
  skill_id: string;
  skill_name: string;
  prompt: string;
  question_type: string;
  difficulty: number;
  options?: string[];
}

export interface StartMasteryCheckResponse {
  id?: string;
  check_id: string;
  activity_attempt_id: string;
  learning_path_node_id: string;
  status: string;
  started_at: string;
  attempt_number: number;
  questions: MasteryCheckQuestionItem[];
}

export interface SkillMasteryOutcomeItem {
  skill_id: string;
  skill_name: string;
  before_mastery: number;
  after_mastery: number;
  mastery_delta: number;
  before_confidence: number;
  after_confidence: number;
  confidence_delta: number;
  evidence_score: number;
  evidence_quality: number;
  proof_strength: number;
  classification: string;
  explanation: string;
}

export interface ProofOfMasteryOutcomeResponse {
  activity_attempt_id: string;
  mastery_check_id?: string;
  learner_id: string;
  evaluated_at: string;
  overall_classification: string;
  overall_explanation: string;
  skill_outcomes: SkillMasteryOutcomeItem[];
}

export interface ActivityAttemptResponse {
  id: string;
  learner_id: string;
  learning_path_id?: string;
  learning_path_node_id: string;
  resource_id?: string | null;
  status: "started" | "completed" | "abandoned" | string;
  started_at: string;
  completed_at?: string | null;
  attempt_number: number;
  completion_percentage: number;
  time_spent_minutes?: number | null;
  resource_title?: string | null;
  resource_url?: string | null;
  skill_name?: string | null;
  submission_data?: Record<string, unknown> | null;
}

export function getRouteForStage(stage?: string | null): string {
  switch (stage) {
    case "GOAL_REQUIRED":
      return "goal";
    case "DIAGNOSTIC_REQUIRED":
    case "DIAGNOSTIC_IN_PROGRESS":
      return "diagnostic";
    case "PATH_SELECTION":
      return "path";
    case "PROOF_REQUIRED":
      return "proof";
    case "ACTIVE_LEARNING":
    case "ADAPTIVE_CONTINUATION":
    default:
      return "overview";
  }
}



