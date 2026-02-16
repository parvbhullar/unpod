/**
 * Get Assets Url
 * @param assetsUrl string
 * @returns fileUrl string
 */
export const getAssetsUrl = (assetsUrl: string): string => {
  return `/${assetsUrl}`;
};

/**
 * Get Image Url
 * @param imageUrl
 * @returns {string}
 */
export const getImageUrl = (imageUrl: string): string => {
  return getAssetsUrl(`images/${imageUrl}`);
};

/**
 * Get Video Url
 * @param videoUrl
 * @returns {string}
 */

export const getVideoUrl = (videoUrl: string): string => {
  return getAssetsUrl(`videos/${videoUrl}`);
};

/**
 * Normalize Url String
 * @param urlSlug
 * @returns {string | undefined}
 */
export const normalizeUrlString = (
  urlSlug: string | null | undefined,
): string | undefined => {
  return urlSlug?.replaceAll('_', ' ').replaceAll('-', ' ');
};

export const queryStringToJSON = (
  queryParams: string,
): Record<string, string> => {
  const pairs = queryParams.split('&');

  const result: Record<string, string> = {};
  pairs.forEach(function (pair) {
    const splitPair = pair.split('=');
    result[splitPair[0]] = decodeURIComponent(splitPair[1] || '');
  });

  return JSON.parse(JSON.stringify(result));
};
