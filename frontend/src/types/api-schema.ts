/**
 * Backend API schema types aligned with FastAPI responses.
 */

// ===== Generation API =====

export interface FeedbackModeSettings {
  enabled: boolean;
  timeout_minutes: number;
  allow_skip: boolean;
}

export interface GenerationOptions {
  priority: 'normal' | 'high';
  webhook_url?: string;
  auto_publish?: boolean | null;
}

export interface GenerateRequest {
  title: string;
  text: string;
  ai_auto_settings: boolean;
  feedback_mode: FeedbackModeSettings;
  options: GenerationOptions;
}

export type SessionCreateRequest = GenerateRequest;

export interface GenerateResponse {
  request_id: string;
  status: string;
  estimated_completion_time?: string | null;
  expected_duration_minutes?: number | null;
  status_url: string;
  websocket_channel?: string | null;
  message?: string | null;
}

export type SessionResponse = GenerateResponse;

export interface SessionStatusResponse {
  session_id: string;
  request_id: string;
  status: string;
  current_phase?: number | null;
  updated_at: string;
  project_id?: string | null;
}

export interface SessionDetailResponse {
  session_id: string;
  request_id: string;
  status: string;
  current_phase?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  retry_count: number;
  phase_results: Array<Record<string, unknown>>;
  preview_versions: Array<Record<string, unknown>>;
  project_id?: string | null;
}

// ===== Feedback API =====

export interface FeedbackPayload {
  feedback_type: string;
  content: Record<string, unknown>;
}

export interface FeedbackRequest {
  phase: number;
  payload: FeedbackPayload;
}

export interface FeedbackResponse {
  status: string;
}

export interface SkipFeedbackRequest {
  phase: number;
  skip_reason: 'satisfied' | 'time_constraint' | 'default_acceptable';
}

export interface SkipFeedbackResponse {
  skipped_phase: number;
  next_phase: number;
  processing_resumed: boolean;
  estimated_completion?: string;
}

// ===== Authentication =====

export interface FirebaseLoginRequest {
  id_token: string;
  device_info?: Record<string, string>;
}

export interface UserInfo {
  id: string;
  email: string;
  display_name?: string | null;
  account_type: string;
  provider: string;
  is_active: boolean;
  photo_url?: string | null;
  created_at?: string | null;
  last_login?: string | null;
  firebase_claims?: Record<string, unknown>;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in: number;
  user: UserInfo;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type?: string;
  expires_in: number;
}

// ===== Common API Wrapper =====

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

// ===== Manga project API =====

export interface MangaWorkItem {
  manga_id: string;
  title: string;
  status: string;
  pages?: number | null;
  style?: string | null;
  created_at: string;
  updated_at: string;
  thumbnail_url?: string | null;
  size_bytes?: number | null;
}

export interface PaginationResponse {
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface MangaWorksListResponse {
  items: MangaWorkItem[];
  pagination: PaginationResponse;
}

export interface MangaWorkDetailResponse {
  manga_id: string;
  title: string;
  status: string;
  metadata: Record<string, unknown>;
  files: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  expires_at?: string | null;
}

