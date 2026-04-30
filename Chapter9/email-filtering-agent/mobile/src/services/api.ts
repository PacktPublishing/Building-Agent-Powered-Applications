import axios from 'axios';
import {
  DailyReport,
  FollowUpReplyRequest,
  IncomingEmail,
  ProcessEmailResponse,
  QueryResponse,
  UserPreferences,
} from '../types';

// Set EXPO_PUBLIC_API_URL in a .env file at the mobile project root.
// Example:  EXPO_PUBLIC_API_URL=http://192.168.1.10:8000
const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Email processing ──────────────────────────────────────────────────────────

export const emailApi = {
  processEmail: async (
    email: IncomingEmail,
    preferences?: UserPreferences,
  ): Promise<ProcessEmailResponse> => {
    const { data } = await api.post('/api/emails/process', {
      email,
      user_preferences: preferences,
    });
    return data;
  },

  sendFollowUpReply: async (request: FollowUpReplyRequest) => {
    const { data } = await api.post('/api/followup/reply', request);
    return data;
  },

  getFollowUpStatus: async (emailId: string) => {
    const { data } = await api.get(`/api/followups/${emailId}`);
    return data;
  },
};

// ── Reports ───────────────────────────────────────────────────────────────────

export const reportApi = {
  getTodayReport: async (): Promise<DailyReport> => {
    const { data } = await api.get('/api/reports/daily');
    return data;
  },

  getReportByDate: async (date: string): Promise<DailyReport> => {
    const { data } = await api.get(`/api/reports/daily/${date}`);
    return data;
  },

  finalizeReport: async (date?: string): Promise<DailyReport> => {
    const { data } = await api.post('/api/reports/finalize', date ? { date } : {});
    return data;
  },
};

// ── Q&A ───────────────────────────────────────────────────────────────────────

export const queryApi = {
  ask: async (
    question: string,
    sessionId?: string,
    dateRangeDays = 30,
  ): Promise<QueryResponse> => {
    const { data } = await api.post('/api/query', {
      question,
      session_id: sessionId,
      date_range_days: dateRangeDays,
    });
    return data;
  },
};

// ── Device registration ───────────────────────────────────────────────────────

export const deviceApi = {
  register: async (pushToken: string) => {
    const { data } = await api.post('/api/devices/register', { push_token: pushToken });
    return data;
  },

  unregister: async (pushToken: string) => {
    const { data } = await api.delete(`/api/devices/${encodeURIComponent(pushToken)}`);
    return data;
  },
};
