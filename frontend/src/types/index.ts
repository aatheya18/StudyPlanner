export interface StudentProfile {
  id: number;
  display_name: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface StudyPreference {
  id: number;
  profile_id: number;
  preferred_session_minutes: number;
  break_duration_minutes: number;
  maximum_daily_study_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface AvailabilityWindow {
  id?: number;
  profile_id?: number;
  day_of_week: number; // 0=Monday, 6=Sunday
  start_time: string; // "09:00"
  end_time: string;   // "18:00"
  is_active: boolean;
}

export interface Subject {
  id: number;
  profile_id: number;
  name: string;
  description?: string;
  color: string;
  task_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  profile_id: number;
  subject_id: number;
  title: string;
  description?: string;
  task_type: string; // 'assignment' | 'revision' | 'reading' | 'practice'
  due_at: string;
  earliest_start_at?: string;
  estimated_duration_minutes: number;
  priority: 'Low' | 'Medium' | 'High';
  status: 'Pending' | 'In Progress' | 'Completed';
  created_at: string;
  updated_at: string;
  subject_name?: string;
  subject_color?: string;
  scheduled_duration_minutes?: number;
  completed_duration_minutes?: number;
}

export interface StudySession {
  id: number;
  task_id: number;
  start_at: string;
  end_at: string;
  status: 'Scheduled' | 'Completed' | 'Skipped';
  actual_duration_minutes?: number;
  created_at: string;
  updated_at: string;
  task_title?: string;
  subject_name?: string;
  subject_color?: string;
}

export interface UnscheduledTaskInfo {
  task_id: number;
  title: string;
  reason: string;
}

export interface ScheduleGenerateResponse {
  sessions_created: StudySession[];
  unscheduled_tasks: UnscheduledTaskInfo[];
  total_slots_used_minutes: number;
  message: string;
}

export interface WeeklyProgressPoint {
  day: string;
  date: string;
  planned_minutes: number;
  completed_minutes: number;
}

export interface DashboardSummary {
  today_sessions: StudySession[];
  tasks_due_soon: Task[];
  overdue_tasks: Task[];
  pending_tasks_count: number;
  completed_tasks_count: number;
  total_planned_minutes: number;
  total_completed_minutes: number;
  weekly_progress: WeeklyProgressPoint[];
}

export interface ReminderItem {
  id: string;
  type: 'upcoming_session' | 'approaching_deadline' | 'overdue_task';
  title: string;
  message: string;
  due_or_start_at: string;
  urgency: 'high' | 'medium' | 'low';
  entity_id: number;
}

export interface RemindersResponse {
  reminders: ReminderItem[];
  count: number;
}

export interface Recommendation {
  id: number;
  task_id: number;
  task_title: string;
  subject_name: string;
  subject_color: string;
  recommended_start_at: string;
  recommended_end_at: string;
  suitability_score?: number;
  model_version: string;
  explanation: string;
  status: 'Pending' | 'Accepted' | 'Rejected';
  created_at: string;
}

export interface ModelStatus {
  model_loaded: boolean;
  model_version: string;
  model_type: string;
  status_detail: string;
  training_sample_count?: number;
  test_accuracy?: number;
  test_f1?: number;
  test_roc_auc?: number;
}
