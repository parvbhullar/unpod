export const isEmptyObject = (obj: Record<string, unknown>): boolean => {
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      return false;
    }
  }
  return true;
};

export const isValidEmail = (value: string | null | undefined): boolean => {
  return !!value && /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,8}$/i.test(value);
};

export const cleanObject = <T extends Record<string, unknown>>(obj: T): T => {
  for (const propName in obj) {
    if (!obj[propName]) {
      delete obj[propName];
    }
  }
  return obj;
};

export const shallowEqual = (
  object1: Record<string, unknown>,
  object2: Record<string, unknown>,
): boolean => {
  const keys1 = Object.keys(object1);
  const keys2 = Object.keys(object2);
  if (keys1.length !== keys2.length) {
    return false;
  }
  for (const key of keys1) {
    if (object1[key] !== object2[key]) {
      return false;
    }
  }
  return true;
};

export const consoleLog = (...data: unknown[]): void => {
  if (process.env.NODE_ENV !== 'production') {
    console.log('App Log:', ...data);
  } else {
    console.info('App Log:', ...data);
  }
};

export const getRandomNumber = (max: number): number => {
  return Math.floor(Math.random() * max);
};

export const getStringFromHtml = (
  htmlContent: string | null | undefined,
): string => {
  return htmlContent &&
    !isEmptyObject(htmlContent as unknown as Record<string, unknown>)
    ? htmlContent?.replace(/(<([^>]+)>)/gi, '')
    : '';
};

export const removeHtmlAndHeadTags = (
  html: string | null | undefined,
): string | undefined => {
  return html?.replace(
    /<!doctype[^>]*>|<html[^>]*>|<\/html>|<!--if[^>]*>|<head[^>]*>.*?<\/head>|<xml[^>]*>.*?<\/xml>|<body[^>]*>|<\/body>/gs,
    '',
  );
};

export const scrollToPostBottom = (): void => {
  setTimeout(() => {
    const element = document.getElementById('post-reply-end');
    if (element) {
      const offsetTop = element.offsetTop;
      if (offsetTop > window.innerHeight / 2) {
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth',
        });
      }
    }
  }, 100);
};

export const isScrolledToBottom = (offset = 100): boolean => {
  const scrolledTo = window.scrollY + window.innerHeight + offset;

  if (offset > 0) {
    return document.body.scrollHeight < scrolledTo;
  }

  return document.body.scrollHeight === scrolledTo;
};

export const randomId = (): number => Math.trunc(Math.random() * 1000) + 1;

export const isJson = (content: string): boolean => {
  try {
    JSON.parse(content);
  } catch (e) {
    return false;
  }
  return true;
};
