/**
 * Backend API Schema Types - Full Compatibility with FastAPI Pydantic Models
 * AUTO-GENERATED: Keep in sync with backend/app/api/v1/
 */

// ===== GENERATION API TYPES =====

export interface FeedbackModeSettings {
  enabled: boolean;
  timeout_minutes: number;
  allow_skip: boolean;
}

export interface GenerationOptions {
  priority: "normal" | "high";
  webhook_url?: string;
  auto_publish: boolean;
}

export interface SessionCreateRequest {
  title: string;
  text: string;
  ai_auto_settings: boolean;
  feedback_mode: FeedbackModeSettings;
  options: GenerationOptions;
}

export interface SessionResponse {
  request_id: string;
  status: string;
  estimated_completion_time?: string;
  performance_mode: string;
  expected_duration_minutes: number;
  status_url: string;
  sse_url: string;
}

// ===== STATUS API TYPES =====

export interface ModuleDetailResponse {
  module_number: number;
  module_name: string;
  status: string;
  started_at?: string;
  estimated_completion?: string;
  progress_percentage: number;
  processing_mode: string;
}

export interface ModuleHistoryResponse {
  module_number: number;
  module_name: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
}

export interface SessionStatusResponse {
  request_id: string;
  status: string;
  current_module: number;
  total_modules: number;
  module_details: ModuleDetailResponse;
  modules_history: ModuleHistoryResponse[];
  overall_progress: number;
  started_at?: string;
  estimated_completion?: string;
  result_url?: string;
}

// ===== FEEDBACK API TYPES =====

export interface FeedbackContent {
  natural_language?: string;
  quick_option?: "make_brighter" | "more_serious" | "add_detail" | "simplify";
  intensity: number;
  target_elements: string[];
}

export interface FeedbackRequest {
  phase: number;
  feedback_type: "natural_language" | "quick_option" | "skip";
  content: FeedbackContent;
}

export interface ParsedModification {
  type: string;
  target: string;
  direction?: string;
  intensity: number;
  addition?: string;
}

export interface FeedbackResponse {
  feedback_id: string;
  request_id: string;
  phase: number;
  status: string;
  parsed_modifications: ParsedModification[];
  estimated_modification_time: number;
  modification_url: string;
}

export interface SceneContent {
  scene_id: number;
  title: string;
  description: string;
  emotion: string;
  pages: number;
}

export interface StoryStructure {
  theme: string;
  genre: string;
  target_pages: number;
  main_scenes: SceneContent[];
}

export interface PreviewUrls {
  thumbnail: string;
  structure_diagram: string;
}

export interface QuickOption {
  label: string;
  value: string;
}

export interface ModificationOptions {
  quick_options: QuickOption[];
  modifiable_elements: string[];
}

export interface PhasePreviewResponse {
  phase: number;
  phase_name: string;
  content: Record<string, any>;
  preview_urls: PreviewUrls;
  modification_options: ModificationOptions;
  feedback_deadline: string;
}

export interface AppliedModification {
  type: string;
  status: string;
  result_preview?: string;
}

export interface ModificationStatusResponse {
  feedback_id: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  applied_modifications: AppliedModification[];
  estimated_completion: string;
  next_phase_available: boolean;
}

export interface SkipFeedbackRequest {
  phase: number;
  skip_reason: "satisfied" | "time_constraint" | "default_acceptable";
}

export interface SkipFeedbackResponse {
  skipped_phase: number;
  next_phase: number;
  processing_resumed: boolean;
  estimated_completion: string;
}

// ===== AUTHENTICATION API TYPES =====

export interface FirebaseLoginRequest {
  id_token: string;
  device_info?: Record<string, string>;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    username: string;
    display_name: string;
    account_type: "free" | "premium" | "admin";
    provider: "google" | "email";
    is_active: boolean;
    photo_url?: string;
    created_at?: string;
    last_login?: string;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserInfo {
  id: string;
  email: string;
  username: string;
  display_name: string;
  account_type: "free" | "premium" | "admin";
  provider: "google" | "email";
  is_active: boolean;
  photo_url?: string;
  created_at?: string;
  last_login?: string;
  firebase_claims?: Record<string, any>;
  permissions?: Record<string, any>;
}

// ===== COMMON API TYPES =====

export interface ApiErrorDetails {
  field?: string;
  constraint?: string;
  trace_id?: string;
  context?: any;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetails;
    timestamp: string;
    path: string;
  };
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}