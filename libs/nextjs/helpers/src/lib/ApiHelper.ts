/**
 * Sanitize Content
 * @param content any
 * @returns content any
 */
export const sanitizeContent = <T>(content: T): T => {
  if (typeof content === 'string') {
    return content as T;
  }

  return content;
};

type SanitizableValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | FormData
  | Date
  | SanitizableArray
  | SanitizableObject;

type SanitizableObject = {
  [key: string]: SanitizableValue;};

type SanitizableArray = SanitizableValue[];

/**
 * Sanitize a Json Array
 * @param arrayOrObject Array or Object
 * @returns output Array or Object
 */
const sanitizeArrayObject = <T extends SanitizableArray | SanitizableObject>(
  arrayOrObject: T,
): T => {
  const output: SanitizableObject | SanitizableArray = Array.isArray(
    arrayOrObject,
  )
    ? []
    : {};

  // loop for an array
  for (const key in arrayOrObject) {
    const item = arrayOrObject[key as keyof typeof arrayOrObject];
    if (typeof item === 'object' && item instanceof FormData) {
      (output as SanitizableObject)[key] = item;
    } else if (
      typeof item === 'object' &&
      item !== null &&
      typeof (item as unknown as Date).getMonth === 'function'
    ) {
      // Date object - keep as is
      (output as SanitizableObject)[key] = item as SanitizableValue;
    } else if (
      Array.isArray(item) ||
      (typeof item === 'object' && item !== null)
    ) {
      // Array or plain object - recursively sanitize
      (output as SanitizableObject)[key] = sanitizeArrayObject(
        item as SanitizableArray | SanitizableObject,
      );
    } else {
      (output as SanitizableObject)[key] = sanitizeContent(
        item,
      ) as SanitizableValue;
    }
  }

  return output as T;
};

export const sanitizeData = <T>(inputVal: T): T | undefined => {
  try {
    if (typeof inputVal === 'object' && inputVal instanceof FormData) {
      return inputVal;
    }

    if (
      Array.isArray(inputVal) ||
      (typeof inputVal === 'object' && inputVal !== null)
    ) {
      return sanitizeArrayObject(
        inputVal as unknown as SanitizableArray | SanitizableObject,
      ) as T;
    }

    return sanitizeContent(inputVal);
  } catch (e) {
    console.log('parse error', e);
    return undefined;
  }
};

export const isRequestSuccessful = (code: number): boolean => {
  return code >= 200 && code <= 204;
};
