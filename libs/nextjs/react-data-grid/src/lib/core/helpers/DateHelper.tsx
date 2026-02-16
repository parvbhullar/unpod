import dayjs from 'dayjs';

export const getDateObject = (dateString?: string, format = 'YYYY-MM-DD') => {
  if (dateString) {
    return dayjs(dateString, format);
  }

  return dayjs();
};
