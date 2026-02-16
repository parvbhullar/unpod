export const getMachineName = (string: string) => {
  return string
    .toLowerCase()
    .replace(/ /g, '_')
    .replace(/-/g, '_')
    .replace(/[^\w-]+/g, '');
};
