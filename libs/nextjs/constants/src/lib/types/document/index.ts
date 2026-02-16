export type Document = {
  document_id?: string;
  name?: string;
  title?: string;
  description?: string;
  content?: string;
  created?: string;
  url?: string;
  seen?: boolean;
  meta?: {
    source_url?: string;
    siteUrl?: string;
    [key: string]: unknown;
  };
  labels?: string[];
  overview?: {
    summary?: string;
    analytics?: {
      avg_call_duration?: string;
      response_rate?: string;
      preferred_time?: string;
      total_calls?: number;
      connected_calls?: number;
      last_connected?: string;
      sentiment?: string | null;
      [key: string]: unknown;
    };
    profile_status?: string;
    recent_conversations?: Array<{
      date?: string;
      summary?: string;
      [key: string]: unknown;
    }>;
    profile_summary?: {
      tone?: string;
      engagement?: string;
      interest_level?: string;
      objections?: string[];
      questions_asked?: string[];
      pain_points?: string[];
      outcome?: string;
      next_action?: string;
      callback_requested?: boolean;
      callback_time?: string | null;
      summary_text?: string;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
