import dayjs, { Dayjs, ManipulateType } from 'dayjs';
import advancedFormat from 'dayjs/plugin/advancedFormat';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import localeData from 'dayjs/plugin/localeData';
import weekday from 'dayjs/plugin/weekday';
import weekOfYear from 'dayjs/plugin/weekOfYear';
import weekYear from 'dayjs/plugin/weekYear';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';

dayjs.extend(customParseFormat);
dayjs.extend(advancedFormat);
dayjs.extend(weekday);
dayjs.extend(localeData);
dayjs.extend(weekOfYear);
dayjs.extend(weekYear);
dayjs.extend(relativeTime);
dayjs.extend(utc);

type DateInput = string | number | Date | Dayjs | null | undefined;

/**
 * Get Custom Date Time with provided format
 * @param dateObject
 * @param value
 * @param unit
 * @param format
 * @param returnType string
 * @returns {Dayjs|string} dayjs object or formatted date string
 */
export function getCustomDateTime(
  dateObject: DateInput,
  value?: number,
  unit?: ManipulateType,
  format?: string,
  returnType?: 'date',
): string;
export function getCustomDateTime(
  dateObject: DateInput,
  value: number,
  unit: ManipulateType,
  format: string,
  returnType: 'dayjs',
): Dayjs;
export function getCustomDateTime(
  dateObject: DateInput,
  value = 0,
  unit: ManipulateType = 'days',
  format = 'YYYY-MM-DD',
  returnType: 'date' | 'dayjs' = 'date',
): string | Dayjs {
  if (returnType === 'date') {
    if (value === 0) {
      return dayjs.utc(dateObject).format(format);
    } else {
      return dayjs.utc(dateObject).add(value, unit).format(format);
    }
  } else {
    if (value === 0) {
      return dayjs.utc(dateObject);
    } else {
      return dayjs.utc(dateObject).add(value, unit);
    }
  }
}

/**
 * Change Date string format
 * @param dateString string
 * @param currentFormat string
 * @param newFormat string
 * @returns {string} string
 */
export const changeDateStringFormat = (
  dateString: string | null | undefined,
  currentFormat = 'YYYY-MM-DD',
  newFormat = 'DD-MM-YYYY',
): string => {
  if (dateString) {
    const dateObject = dayjs.utc(dateString, currentFormat);
    return dayjs(dateObject).local().format(newFormat);
  }

  return '--';
};

/**
 * Get formatted date
 * @param dateObject Date Object
 * @param format string
 * @param isUTC0 boolean
 * @returns {string | undefined} string
 */
export const getFormattedDate = (
  dateObject: DateInput,
  format = 'DD-MM-YYYY',
  isUTC0 = false,
): string | undefined => {
  if (dateObject) {
    if (isUTC0) {
      return getLocalLocalTimeFromUTC(dateObject).format(format);
    }
    return dayjs(dateObject).format(format);
  }
  return undefined;
};

export const getLocalLocalTimeFromUTC = (dateObject: DateInput): Dayjs => {
  return dayjs.utc(dateObject).local();
};

/**
 * Get Date object of Date string
 * @param dateString string
 * @param format string
 * @returns {Dayjs} Date Object
 */
export const getDateObject = (dateString = '', format = ''): Dayjs => {
  if (dateString) {
    return dayjs(dateString, format);
  }

  return dayjs();
};

export const getTimeFromNow = (
  date: DateInput,
  format = 'YYYY-MM-DD HH:mm:ss',
): string => {
  if (!date) {
    return '';
  }
  return dayjs.utc(date, format).fromNow();
};

export type ScheduleOption = {
  key: string;
  title: string;
  date: string;
  time: string;
};

/**
 * Get Schedule Options
 * @returns {Array} array
 */
export const getScheduleOptions = (): ScheduleOption[] => {
  const today = dayjs();
  const tomorrow = today.add(1, 'days');
  const nextDate = dayjs(
    `${tomorrow.format('YYYY-MM-DD')} 09:00:00`,
    'YYYY-MM-DD HH:mm:ss',
  );

  const options: ScheduleOption[] = [
    {
      key: nextDate.format('YYYY-MM-DD'),
      title: 'Tomorrow at 9:00 AM',
      date: nextDate.format('YYYY-MM-DD'),
      time: nextDate.format('HH:mm'),
    },
  ];

  for (let i = 1; i < 30; i++) {
    const nextDay = tomorrow.add(i, 'days');
    const nextDateInner = dayjs(
      `${nextDay.format('YYYY-MM-DD')} 09:00:00`,
      'YYYY-MM-DD HH:mm:ss',
    );

    const date = nextDateInner.format('YYYY-MM-DD');
    const time = nextDateInner.format('HH:mm');

    options.push({
      key: date,
      title: `${nextDateInner.format(i < 6 ? 'dddd' : 'MMMM D')} at 9:00 AM`,
      date,
      time,
    });
  }

  return options;
};

export const formatDateYearMonth = (dateStr: string): string => {
  const [year, month] = dateStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1);
  return date.toLocaleString('en-US', { month: 'long', year: 'numeric' });
};

export const getUtcTimestamp = (
  date: Date | Dayjs,
  inSeconds = true,
): number => {
  return inSeconds ? Math.floor(date.valueOf() / 1000) : date.valueOf();
};

export const formatSecToTime = (seconds: number | string): string => {
  const sec = parseInt(String(seconds), 10);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) {
    return `${h}Hr ${m}Min ${s}Sec`;
  } else if (m > 0) {
    return `${m}Min ${s}Sec`;
  } else {
    return `0Min ${s}Sec`;
  }
};

export const formatSecToMin = (seconds: number | string): string => {
  if (seconds === -1) {
    return '';
  }
  const sec = parseInt(String(seconds), 10);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60 || '0';
  if (m > 0) {
    return `${h * 60 + m} Min`;
  } else {
    return `${s} Sec`;
  }
};

/**
 * Format duration in seconds to "X min Y sec" format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string (e.g., "5 min 30 sec", "45 sec")
 */
export const formatDuration = (
  seconds: number | string | null | undefined,
): string => {
  if (!seconds || seconds === 0 || isNaN(Number(seconds))) return 'N/A';
  const totalSeconds = parseInt(String(seconds), 10);
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds} sec`;
  } else if (remainingSeconds === 0) {
    return `${minutes} min`;
  } else {
    return `${minutes} min ${remainingSeconds} sec`;
  }
};

/**
 * Get the browser's timezone offset
 * @returns {string} Timezone offset string (e.g., '+05:30', '-08:00')
 */
export const getBrowserTimezone = (): string => {
  const offsetMinutes = new Date().getTimezoneOffset();
  const sign = offsetMinutes <= 0 ? '+' : '-';
  const absOffset = Math.abs(offsetMinutes);
  const hours = String(Math.floor(absOffset / 60)).padStart(2, '0');
  const minutes = String(absOffset % 60).padStart(2, '0');
  return `${sign}${hours}:${minutes}`;
};

export const getTimeBySeconds = (seconds: number): string => {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
};
