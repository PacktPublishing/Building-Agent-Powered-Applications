export type EmailCategory = 'urgent' | 'important' | 'requires_follow_up' | 'ignore';

export interface IncomingEmail {
  id?: string;
  sender: string;
  sender_name?: string;
  subject: string;
  body: string;
  thread_id?: string;
  received_at?: string;
}

export interface UserPreferences {
  urgent_keywords: string[];
  important_senders: string[];
  ignore_keywords: string[];
  custom_rules?: string;
}

export interface ProcessEmailResponse {
  email_id: string;
  category: EmailCategory;
  actions_taken: string[];
  follow_up_message?: string;
  summary?: string;
}

export interface EmailSummary {
  email_id: string;
  sender: string;
  subject: string;
  summary: string;
  received_at: string;
}

export interface DailyReport {
  date: string;
  summaries: EmailSummary[];
  urgent_count: number;
  important_count: number;
  ignored_count: number;
  follow_up_count: number;
  finalized: boolean;
  finalized_at?: string;
}

export interface QueryResponse {
  answer: string;
  session_id: string;
  sources: string[];
}

export interface UrgentNotification {
  id: string;
  subject: string;
  sender: string;
  email_id: string;
  received_at: string;
}

export interface FollowUpReplyRequest {
  thread_id: string;
  sender: string;
  body: string;
}
