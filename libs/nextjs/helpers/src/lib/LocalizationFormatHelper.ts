export type FormatMessageFn = {
  (descriptor: { id: string; defaultMessage?: string }): string;};

export const getRoleLabel = (
  role: string,
  formatMessage: FormatMessageFn,
): string => {
  return formatMessage({
    id: `role.${role}`,
    defaultMessage: role,
  });
};

export type LocalizableOption = {
  key?: string;
  label?: string;
  description?: string;
  desc?: string;
  [key: string]: unknown;};

export type LocalizedOption = LocalizableOption & {
  label: string;
  description: string;};

// for array localization formatting
export const getLocalizedOptions = (
  options: LocalizableOption[] = [],
  formatMessage: FormatMessageFn,
): LocalizedOption[] => {
  return options.map((item) => {
    const labelId = item.label;
    const descriptionId = item.description ? item.description : item.desc;

    return {
      ...item,
      label: labelId
        ? formatMessage({ id: labelId, defaultMessage: item.key || '' })
        : '',
      description: descriptionId
        ? formatMessage({ id: descriptionId, defaultMessage: '' })
        : '',
    };
  });
};

export type StatusConfigValue = {
  name: string;
  [key: string]: unknown;};

export type StatusOption = StatusConfigValue & {
  key: string;};

// for obj localization formatting
export const getStatusOptionsFromConfig = (
  statusConfig: Record<string, StatusConfigValue> = {},
  formatMessage: FormatMessageFn,
): StatusOption[] => {
  return Object.entries(statusConfig).map(([key, value]) => ({
    key,
    ...value,
    name: formatMessage({ id: value.name }),
  }));
};

export type CallStatusConfigValue = {
  label: string;
  [key: string]: unknown;};

// for configuration obj localization formatting
export const localizeCallStatusLabels = (
  statusConfig: Record<string, CallStatusConfigValue> = {},
  formatMessage: FormatMessageFn,
): Record<string, CallStatusConfigValue> => {
  return Object.fromEntries(
    Object.entries(statusConfig).map(([key, value]) => [
      key,
      {
        ...value,
        label: formatMessage({ id: value.label }),
      },
    ]),
  );
};
