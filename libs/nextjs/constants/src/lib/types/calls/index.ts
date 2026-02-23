type TranscriptMessage = {
  role?: string;
  content?: string;
  user_id?: string | null;
  timestamp?: string;
  [key: string]: unknown;
};

type ProfileSummary = {
  interest_level?: string | number;
  outcome?: string;
  tone?: string;
  engagement?: string;
  questions_asked?: string[];
  next_action?: string | string[];
  [key: string]: unknown;
};

type PostCallData = {
  summary?: {
    summary?: string;
  };
  classification?: {
    labels?: string[];
  };
  profile_summary?: ProfileSummary;
  follow_up?: {
    required?: boolean | 'true' | 'false';
    time?: string;
    status?: string;
    date?: string;
    reason?: string;
    [key: string]: unknown;
  } | null;
  structured_data?: string | { [key: string]: unknown };
  [key: string]: unknown;
};

export type CallItem = {
  name: string;
  number: string;
  task_id: string;
  status: string;
  call_type: string;
  created: string;
};

export type Call = {
  status?: string;
  created?: string;
  modified?: string;
  task_id?: string | number;
  assignee?: string;
  recording_url?: string;
  task?: {
    objective?: string;
    [key: string]: unknown;
  };
  user_info?: {
    full_name?: string;
    [key: string]: unknown;
  };
  input?: {
    name?: string;
    contact_number?: string;
    call_type?: string;
    [key: string]: unknown;
  };
  output?: {
    recording_url?: string;
    error?: string;
    call_type?: string;
    call_status?: string;
    customer?: string;
    cost?: number;
    duration?: number;
    santiment?: string | number;
    transcript?:
      | string
      | TranscriptMessage[]
      | {
      messages?: TranscriptMessage[];
      [key: string]: unknown;
    };
    post_call_data?: PostCallData;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
