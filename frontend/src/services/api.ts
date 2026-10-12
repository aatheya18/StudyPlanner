import {
  StudentProfile,
  StudyPreference,
  AvailabilityWindow,
  Subject,
  Task,
  StudySession,
  ScheduleGenerateResponse,
  DashboardSummary,
  RemindersResponse,
  Recommendation,
  ModelStatus
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `Request failed (${res.status})`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMsg);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const api = {
  // Profile & Preferences
  getProfile: (): Promise<StudentProfile> =>
    fetch(`${API_BASE_URL}/api/profile`).then(handleResponse<StudentProfile>),

  updateProfile: (data: Partial<StudentProfile>): Promise<StudentProfile> =>
    fetch(`${API_BASE_URL}/api/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<StudentProfile>),

  getPreferences: (): Promise<StudyPreference> =>
    fetch(`${API_BASE_URL}/api/preferences`).then(handleResponse<StudyPreference>),

  updatePreferences: (data: Partial<StudyPreference>): Promise<StudyPreference> =>
    fetch(`${API_BASE_URL}/api/preferences`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<StudyPreference>),

  getAvailability: (): Promise<AvailabilityWindow[]> =>
    fetch(`${API_BASE_URL}/api/availability`).then(handleResponse<AvailabilityWindow[]>),

  updateAvailability: (windows: AvailabilityWindow[]): Promise<AvailabilityWindow[]> =>
    fetch(`${API_BASE_URL}/api/availability`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(windows)
    }).then(handleResponse<AvailabilityWindow[]>),

  // Subjects
  getSubjects: (): Promise<Subject[]> =>
    fetch(`${API_BASE_URL}/api/subjects`).then(handleResponse<Subject[]>),

  createSubject: (data: Omit<Subject, 'id' | 'profile_id' | 'created_at' | 'updated_at' | 'task_count'>): Promise<Subject> =>
    fetch(`${API_BASE_URL}/api/subjects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<Subject>),

  updateSubject: (id: number, data: Partial<Subject>): Promise<Subject> =>
    fetch(`${API_BASE_URL}/api/subjects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<Subject>),

  deleteSubject: (id: number, force: boolean = false): Promise<void> =>
    fetch(`${API_BASE_URL}/api/subjects/${id}?force=${force}`, {
      method: 'DELETE'
    }).then(handleResponse<void>),

  // Tasks
  getTasks: (params?: { subject_id?: number; status?: string; priority?: string; search?: string; sort_by?: string; sort_order?: string }): Promise<Task[]> => {
    const query = new URLSearchParams();
    if (params?.subject_id) query.append('subject_id', params.subject_id.toString());
    if (params?.status) query.append('status', params.status);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.search) query.append('search', params.search);
    if (params?.sort_by) query.append('sort_by', params.sort_by);
    if (params?.sort_order) query.append('sort_order', params.sort_order);

    return fetch(`${API_BASE_URL}/api/tasks?${query.toString()}`).then(handleResponse<Task[]>);
  },

  createTask: (data: Partial<Task>): Promise<Task> =>
    fetch(`${API_BASE_URL}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<Task>),

  updateTask: (id: number, data: Partial<Task>): Promise<Task> =>
    fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<Task>),

  deleteTask: (id: number): Promise<void> =>
    fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: 'DELETE'
    }).then(handleResponse<void>),

  // Sessions & Scheduling
  getSessions: (params?: { start?: string; end?: string; task_id?: number; status?: string }): Promise<StudySession[]> => {
    const query = new URLSearchParams();
    if (params?.start) query.append('start', params.start);
    if (params?.end) query.append('end', params.end);
    if (params?.task_id) query.append('task_id', params.task_id.toString());
    if (params?.status) query.append('status', params.status);

    return fetch(`${API_BASE_URL}/api/sessions?${query.toString()}`).then(handleResponse<StudySession[]>);
  },

  generateSchedule: (data: { start_date?: string; horizon_days?: number; clear_existing_scheduled?: boolean }): Promise<ScheduleGenerateResponse> =>
    fetch(`${API_BASE_URL}/api/schedules/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<ScheduleGenerateResponse>),

  updateSession: (id: number, data: Partial<StudySession>): Promise<StudySession> =>
    fetch(`${API_BASE_URL}/api/sessions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<StudySession>),

  completeSession: (id: number, data: { actual_duration_minutes?: number; mark_task_completed?: boolean }): Promise<StudySession> =>
    fetch(`${API_BASE_URL}/api/sessions/${id}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<StudySession>),

  skipSession: (id: number): Promise<StudySession> =>
    fetch(`${API_BASE_URL}/api/sessions/${id}/skip`, {
      method: 'POST'
    }).then(handleResponse<StudySession>),

  deleteSession: (id: number): Promise<void> =>
    fetch(`${API_BASE_URL}/api/sessions/${id}`, {
      method: 'DELETE'
    }).then(handleResponse<void>),

  // Dashboard & Reminders
  getDashboard: (): Promise<DashboardSummary> =>
    fetch(`${API_BASE_URL}/api/dashboard`).then(handleResponse<DashboardSummary>),

  getReminders: (): Promise<RemindersResponse> =>
    fetch(`${API_BASE_URL}/api/reminders`).then(handleResponse<RemindersResponse>),

  // AI Recommendations
  getAIStatus: (): Promise<ModelStatus> =>
    fetch(`${API_BASE_URL}/api/ai/status`).then(handleResponse<ModelStatus>),

  generateRecommendations: (data: { horizon_days?: number; candidate_slots_per_task?: number }): Promise<Recommendation[]> =>
    fetch(`${API_BASE_URL}/api/ai/recommendations/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse<Recommendation[]>),

  getRecommendations: (status: string = 'Pending'): Promise<Recommendation[]> =>
    fetch(`${API_BASE_URL}/api/ai/recommendations?status=${status}`).then(handleResponse<Recommendation[]>),

  acceptRecommendation: (id: number, note?: string): Promise<StudySession> =>
    fetch(`${API_BASE_URL}/api/ai/recommendations/${id}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note })
    }).then(handleResponse<StudySession>),

  rejectRecommendation: (id: number, note?: string): Promise<{ message: string }> =>
    fetch(`${API_BASE_URL}/api/ai/recommendations/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note })
    }).then(handleResponse<{ message: string }>),
};
