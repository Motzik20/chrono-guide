export interface TaskBase {
  title: string;
  description: string;
  expected_duration_minutes: number;
  tips: string[];
  priority?: number;
  deadline?: string | null;
}

export interface TaskDraft extends TaskBase {
  // No additional fields - same as base
}

export interface Task extends TaskBase {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}
