export const ACCESS_ROLE = {
  OWNER: 'owner',
  EDITOR: 'editor',
  VIEWER: 'viewer',
  GUEST: 'guest',
} as const;

export type AccessRoleType = (typeof ACCESS_ROLE)[keyof typeof ACCESS_ROLE];

export const POST_TYPE = {
  POST: 'post',
  ARTICLE: 'article',
  QUESTION: 'question',
  CHALLENGE: 'challenge',
  BOUNTY: 'bounty',
  EVENT: 'event',
  WEBINAR: 'webinar',
  TASK: 'task',
  ASK: 'ask',
  NOTEBOOK: 'notebook',
} as const;

export type PostTypeValue = (typeof POST_TYPE)[keyof typeof POST_TYPE];

export const POST_CONTENT_TYPE = {
  TEXT: 'text',
  VIDEO: 'video',
  AUDIO: 'audio',
  VOICE: 'voice',
  VIDEO_STREAM: 'video_stream',
  AUDIO_STREAM: 'audio_stream',
} as const;

export type PostContentTypeValue =
  (typeof POST_CONTENT_TYPE)[keyof typeof POST_CONTENT_TYPE];

export const POST_EXTRA_CONTENT_TYPE = {
  IMAGE: 'image',
  POLL: 'poll',
  LOCATION: 'location',
  METRIC: 'metric',
} as const;

export type PostExtraContentTypeValue =
  (typeof POST_EXTRA_CONTENT_TYPE)[keyof typeof POST_EXTRA_CONTENT_TYPE];

export const TAG_COLORS = [
  'processing',
  'success',
  'warning',
  'error',
  'magenta',
  'red',
  'volcano',
  'orange',
  'purple',
  'green',
] as const;

export type TagColorType = (typeof TAG_COLORS)[number];
