export type CallStatusItem = {
  color: string;
  label: string;
};

export const CALL_STATUS: Record<string, CallStatusItem> = {
  completed: {color: 'badge-success', label: 'callLogs.completed'},
  success: {color: 'badge-success', label: 'callLogs.success'},
  ANSWERED: {color: 'badge-success', label: 'callLogs.answered'},
  CANCEL: {color: 'badge-warning', label: 'callLogs.cancel'},
  CONGESTION: {color: 'badge-warning', label: 'callLogs.congestion'},
  FAILURE: {color: 'badge-error', label: 'callLogs.failure'},
  failed: {color: 'badge-error', label: 'callLogs.failed'},
  FAILED: {color: 'badge-error', label: 'callLogs.failed'},
  REJECTED: {color: 'badge-error', label: 'callLogs.rejected'},
};

export type CallEndReasonItem = {
  label: string;
};

export const CALL_END_REASONS: Record<string, CallEndReasonItem> = {
  'customer-ended-call': {label: 'Call Ended'},
};
