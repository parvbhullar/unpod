export const NAME_REGX = /^(?=(?:^\w))([a-zA-Z . &]+)(?<=[^ ])$/;
export const ALPHA_NUMERIC_REGX = /^[a-z0-9A-Z\s]+$/;
export const NUMERIC_REGX = /^\d+$/;
export const ALPHA_REGEX = /^[A-Za-z ]+$/;
export const alphaNumericDot =
  /^(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&^_-])[A-Za-z\d@$!%*#?&^_-]{8,}$/;
export const PASSWORD_REGX =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&;^[\]{}_-])[A-Za-z\d@$!%*#?&;^[\]{}_-]{8,}$/;
export const PIN_CODE_REGX = /^[1-9][0-9]{5}$/;
export const MOBILE_REGX =
  // /^(?:\s+|)((0|(?:(\+|)91))(?:\s|-)*(?:(?:\d(?:\s|-)*\d{9})|(?:\d{2}(?:\s|-)*\d{8})|(?:\d{3}(?:\s|-)*\d{7}))|\d{10})(?:\s+|)$/;
  /^([0-9]{6,11})$/;

export const EMAIL_REGX =
  /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

export const URL_REGX =
  /[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)?/gi;

export const PILOT_HANDLE_REGX = /^[a-z0-9A-Z_-]+$/;

export const URL_WITH_PROTOCOL_REGX =
  /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/[^\s]*)?$/;

export const URL_WITH_WEBSOCKET_PROTOCOL_REGX =
  /^(wss?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/[^\s]*)?$/;
