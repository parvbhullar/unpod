export const saveDraftData = (dataKey: string, data: unknown): void => {
  localStorage.setItem(dataKey, JSON.stringify(data));
  const parsedKeys: string[] =
    JSON.parse(localStorage.getItem('draft-keys') || 'null') || [];

  if (!parsedKeys.find((key) => key === dataKey)) {
    parsedKeys.push(dataKey);
    localStorage.setItem('draft-keys', JSON.stringify(parsedKeys));
  }
};

export const getDraftData = <T = unknown>(dataKey: string): T | null => {
  const item = localStorage.getItem(dataKey);
  return item ? JSON.parse(item) : null;
};

export const clearLocalStorage = (): void => {
  const parsedKeys: string[] =
    JSON.parse(localStorage.getItem('draft-keys') || 'null') || [];
  parsedKeys.forEach((key) => {
    localStorage.removeItem(key);
  });
  localStorage.removeItem('draft-keys');
  localStorage.removeItem('web-camera');
  localStorage.removeItem('mic');
};
