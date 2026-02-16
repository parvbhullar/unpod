export type TaskItem = {
  status?: string;
  created?: string;
  input?: {
    name?: string;
    title?: string;
    [key: string]: unknown;
  };
  output?: {
    recording_url?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
