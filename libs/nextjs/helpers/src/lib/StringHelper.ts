/**
 * Clean String
 * @param string
 * @returns {string}
 */
export const cleanString = (string: string | null | undefined): string => {
  if (string) return string.replace(/"/g, '').replace(/,/g, '');

  return '';
};

/**
 * Get Avatar Placeholder String
 * @param string
 * @returns {string}
 */
export const getAvatarPlaceholder = (
  string: string | null | undefined,
): string => {
  if (string) return string.charAt(0).toUpperCase();

  return '';
};

/**
 * Truncate String value
 * @param str
 * @param num
 * @param ellipsis
 * @returns {string}
 */
export const truncateString = (
  str: string | null | undefined,
  num = 16,
  ellipsis = true,
): string => {
  if (!str || str.length <= num) {
    return str || '';
  }

  return str.slice(0, num - 2) + (ellipsis ? '...' : '');
};

export const maskEmail = (email: string): string => {
  return email.replace(
    /^(.)(.*)(.@.*)$/,
    (_, a: string, b: string, c: string) => a + b.replace(/./g, '*') + c,
  );
};

export const formatColumnName = (text: string | null | undefined): string => {
  if (text) return capitalizedString(text.replaceAll('_', ' '));
  return '-';
};

export const upperCaseString = (text: string | null | undefined): string => {
  if (text) return text.toUpperCase();
  return '-';
};

export const capitalizedString = (text: string | null | undefined): string => {
  if (text) return text.charAt(0).toUpperCase() + text.slice(1);
  return '-';
};

export const capitalizedAllWords = (words: string): string => {
  const wordsArray = words.split(' ');
  let outputString = '';

  for (const word of wordsArray) {
    outputString += `${capitalizedString(word)} `;
  }

  return outputString;
};

export const formatString = (text: string | null | undefined): string => {
  if (text) return text.replaceAll('_', ' & ').toUpperCase();
  return '-';
};

export const removeSpaceFromString = (string: string): string => {
  return string.replace(/ /g, '');
};

export const getRandomColor = (): string => {
  const letters = '0123456789ABCDEF';
  let color = '#';
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
};

export const getFirstLetter = (
  name: string | null | undefined,
): string | undefined => {
  if (typeof name !== 'string') {
    return;
  }
  let initials: string;
  const nameSplit = name?.split(' ') || [];
  const nameLength = nameSplit.length;
  if (nameLength > 1) {
    initials = nameSplit[0].substring(0, 1) + nameSplit[1].substring(0, 1);
  } else if (nameLength === 1) {
    initials = name!.substring(0, 2);
  } else return;

  return initials.toUpperCase();
};

export const getMachineName = (string: string): string => {
  return string
    .toLowerCase()
    .replace(/ /g, '_')
    .replace(/-/g, '_')
    .replace(/[^\w-]+/g, '');
};

export const getJsonString = (string: string): string => {
  try {
    return JSON.stringify(JSON.parse(string.toString()), undefined, 4);
  } catch (e) {
    return string;
  }
};

export const convertMachineNameToName = (
  string: string | null | undefined,
): string | undefined => {
  return string?.replace(/-/g, ' ').replace(/_/g, ' ');
};

export const generateHandle = (input = 'new', length = 12): string => {
  const characters = `abcdefghijklmnopqrstuvwxyz0123456789`;
  let randomString = '';
  for (let i = 0; i < length; i++) {
    randomString += characters.charAt(
      Math.floor(Math.random() * characters.length),
    );
  }

  // Generate handle by replacing non-alphanumeric characters with hyphens and max limit 99 - length and appending the random string
  return `${input
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '-')
    .substring(0, 99 - length - 1)}-${randomString}`;
};
