// utils/responsiveHelpers.js

const iconSizeByBreakpoint = {
  xs: 12,
  sm: 14,
  md: 18,
  lg: 18,
  xl: 18,
  xxl: 18,
};

const avatarIconSizeByBreakpoint = {
  xs: 16,
  sm: 18,
  md: 24,
  lg: 24,
  xl: 24,
  xxl: 32,
};

const avatarSizeByBreakpoint = {
  xs: 22,
  sm: 32,
  md: 30,
  lg: 32,
  xl: 34,
  xxl: 38,
};

type Breakpoint = keyof typeof iconSizeByBreakpoint;
type ScreenMap = Partial<Record<Breakpoint, boolean>>;

export const getIconSize = (screens: ScreenMap) => {
  const currentKey =
    (Object.keys(iconSizeByBreakpoint) as Breakpoint[]).find(
      (key) => screens[key],
    ) || 'lg';
  return iconSizeByBreakpoint[currentKey];
};

export const getAvatarIconSize = (screens: ScreenMap) => {
  const currentKey =
    (Object.keys(avatarIconSizeByBreakpoint) as Breakpoint[]).find(
      (key) => screens[key],
    ) || 'lg';
  return avatarIconSizeByBreakpoint[currentKey];
};

export const getAvatarSize = (screens: ScreenMap) => {
  const currentKey =
    (Object.keys(avatarSizeByBreakpoint) as Breakpoint[]).find(
      (key) => screens[key],
    ) || 'lg';
  return avatarSizeByBreakpoint[currentKey];
};
