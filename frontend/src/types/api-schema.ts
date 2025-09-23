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
  status_url: string;  // Required field
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

// ===== HITL Feedback API (Aligned with backend schemas/hitl.py) =====

export interface UserFeedbackRequest {
  phase: number;  // 1-7
  feedback_type: 'approval' | 'modification' | 'skip';
  selected_options?: string[] | null;
  natural_language_input?: string | null;
  user_satisfaction_score?: number | null;  // 1.0-5.0
  processing_time_ms?: number | null;
}

export interface FeedbackOptionResponse {
  id: string;
  phase: number;
  option_key: string;
  option_label: string;
  option_description?: string | null;
  option_category?: string | null;
  display_order: number;
  is_active: boolean;
}

export interface FeedbackOptionsResponse {
  phase: number;
  options: FeedbackOptionResponse[];
  total_count: number;
}

export interface HITLFeedbackResponse {
  success: boolean;
  message: string;
  processing_status: string;
  estimated_completion_time?: string | null;
  feedback_id?: string | null;
}

export interface FeedbackStateResponse {
  session_id: string;
  phase: number;
  state: string;  // waiting, received, processing, completed, timeout
  remaining_time_seconds?: number | null;
  feedback_started_at: string;
  feedback_timeout_at?: string | null;
  feedback_received_at?: string | null;
  preview_data?: Record<string, unknown> | null;
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

export interface MangaProjectItem {
  manga_id: string;
  title: string;
  status: string;
  pages?: number | null;
  style?: string | null;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Pagination {
  page: number;
  limit: number;
  total_items: number;  // Aligned with backend
  total_pages: number;  // Aligned with backend
  has_next: boolean;
  has_previous: boolean;  // Aligned with backend
}

export interface MangaProjectListResponse {
  items: MangaProjectItem[];
  pagination: Pagination;
}

export interface MangaProjectDetailResponse {
  manga_id: string;
  title: string;
  status: string;
  description?: string | null;
  metadata?: Record<string, unknown> | null;
  settings?: Record<string, unknown> | null;
  total_pages?: number | null;
  style?: string | null;
  visibility: string;
  expires_at?: string | null;
  files?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  user_id?: string | null;
  session_id?: string | null;
}

// ===== Message API (Aligned with backend schemas/manga.py) =====

export interface MessageRequest {
  content: string;  // 1-5000 chars
  message_type?: string;  // default: "user"
  phase?: number | null;
  metadata?: Record<string, unknown> | null;
}

export interface MessageResponse {
  id: string;
  session_id: string;
  message_type: string;
  content: string;
  phase?: number | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface MessagesListResponse {
  messages: MessageResponse[];
  total: number;
  has_more: boolean;
}

// ===== Phase Preview API (Aligned with backend schemas/manga.py) =====

export interface PhasePreviewUpdate {
  preview_type?: string;  // default: "text"
  content?: string | null;
  image_url?: string | null;
  document_url?: string | null;
  progress: number;  // 0-100
  status?: string;  // default: "processing"
  metadata?: Record<string, unknown> | null;
}

export interface PhasePreviewResponse {
  id: string;
  session_id: string;
  phase_number: number;
  preview_type: string;
  content?: string | null;
  image_url?: string | null;
  document_url?: string | null;
  progress: number;
  status: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// ===== Error Handling =====

export interface PhaseError {
  code: string;
  message: string;
  details?: string;
  timestamp: Date;
  retryable: boolean;
  retryCount: number;
  errorType: 'network' | 'authentication' | 'validation' | 'server' | 'timeout' | 'unknown';
  suggestions?: string[];
}

export interface ErrorState {
  [phaseId: number]: {
    error: PhaseError | null;
    retryAttempts: number;
    lastRetryAt: Date | null;
    isRetrying: boolean;
    autoRetryEnabled: boolean;
  };
}

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors: string[];
}

// Legacy interfaces for backward compatibility
export interface MangaWorkItem extends MangaProjectItem {}
export interface PaginationResponse extends Pagination {
  // Already aligned with backend structure
  total: number;    // Legacy alias for total_items
  pages: number;    // Legacy alias for total_pages
  has_prev: boolean;  // Legacy alias for has_previous
}
export interface MangaWorksListResponse extends MangaProjectListResponse {}
export interface MangaWorkDetailResponse extends MangaProjectDetailResponse {
  metadata: Record<string, unknown>;
  files: Record<string, unknown>;
}

