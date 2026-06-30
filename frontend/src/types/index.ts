export interface User {
  id: string;
  email: string;
  role: 'user' | 'admin';
  status: 'active' | 'pending' | 'blocked' | 'suspended' | 'deleted';
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  profile: UserProfile | null;
  settings: UserSettings | null;
}

export interface UserProfile {
  full_name: string;
  avatar_url: string | null;
}

export interface UserSettings {
  theme: string;
  language: string;
  timezone: string;
  notification_preferences: string;
  digest_frequency: string;
  preferred_summary_length: string;
  preferred_language: string;
  ai_personality: string;
  digest_schedule: string;
  memory_enabled: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ApiError {
  success: false;
  message: string;
  error: string;
  details?: unknown;
  request_id?: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_communications: number;
  gmail_messages: number;
  whatsapp_messages: number;
  pending_tasks: number;
  ai_summaries: number;
  connected_platforms: number;
}

export interface ActivityItem {
  id: string;
  type: 'gmail' | 'whatsapp' | 'ai' | 'task' | 'system';
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
}
