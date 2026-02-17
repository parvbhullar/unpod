export type KeyValuePair = {
  key: string;
  value: unknown;
};

/**
 * Converts a list of objects with 'key' and 'value' properties into a dictionary.
 * @param list
 * @returns {Record<string, unknown>}
 */
export const convertListToDictionary = (
  list: KeyValuePair[],
): Record<string, unknown> => {
  return list.reduce(
    (acc, item) => {
      acc[item['key']] = item['value'];
      return acc;
    },
    {} as Record<string, unknown>,
  );
};

/**
 * Converts a dictionary into a list of objects with 'key' and 'value' properties.
 * @param dictionary
 * @returns {Array}
 */
export const convertDictionaryToList = (
  dictionary: Record<string, unknown>,
): KeyValuePair[] => {
  return Object.entries(dictionary).map(([key, value]) => ({
    key,
    value,
  }));
};
