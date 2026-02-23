import {lighten} from 'polished';

// Breakpoint interfaces
type ThemeBreakpoints = {
  xss: number;
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
};

// Font interfaces
type ThemeFontWeight = {
  light: number;
  regular: number;
  medium: number;
  semiBold: number;
  bold: number;
};

type ThemeFontSize = {
  base: string;
  lg: string;
  sm: string;
};

type ThemeFont = {
  family: string;
  weight: ThemeFontWeight;
  size: ThemeFontSize;
};

// Layout interfaces
type ThemeLayoutHeader = {
  height: number;
};

type ThemeLayoutSidebar = {
  width: number;
  collapsedWidth: number;
};

type ThemeLayoutMain = {
  header: ThemeLayoutHeader;
  sidebar: ThemeLayoutSidebar;
};

type ThemeLayout = {
  main: ThemeLayoutMain;
};

// Palette interfaces
type ThemePaletteCommon = {
  black: string;
  white: string;
};

type ThemePaletteText = {
  primary: string;
  secondary: string;
  content: string;
  dark: string;
  light: string;
  heading: string;
  subheading: string;
};

type ThemePaletteBackground = {
  default: string;
  paper: string;
  component: string;
  header: string;
  colorPrimaryBg: string;
  disabled: string;
};

type ThemePalette = {
  common: ThemePaletteCommon;
  primary: string;
  primaryActive: string;
  primaryHover: string;
  primaryActiveHover: string;
  secondary: string;
  success: string;
  error: string;
  warning: string;
  info: string;
  infoText: string;
  infoBorder: string;
  infoBg: string;
  text: ThemePaletteText;
  background: ThemePaletteBackground;
};

// Space interface
type ThemeSpace = {
  xl: string;
  lg: string;
  md: string;
  sm: string;
  xs: string;
  xss: string;
};

// Height rules interface
type ThemeHeightRules = {
  base: string;
  lg: string;
  sm: string;
};

// Border interface
type ThemeBorder = {
  color: string;
  style: string;
  width: string;
};

// Radius interface
type ThemeRadius = {
  base: number;
  sm: number;
  circle: string;
  button: number;
};

// Component interfaces
type ThemeComponentGrid = {
  gutter: number;
};

type ThemeComponentTable = {
  headBackground: string;
  rowHover: string;
};

type ThemeComponentCard = {
  boxShadow: string;
  borderRadius: string;
  headerBgColor: string;
};

type ThemeComponentTabs = {
  bgColor: string;
  hoverBgColor: string;
};

type ThemeComponentCheckbox = {
  borderRadius: string;
};

type ThemeComponent = {
  grid: ThemeComponentGrid;
  table: ThemeComponentTable;
  card: ThemeComponentCard;
  tabs: ThemeComponentTabs;
  checkbox: ThemeComponentCheckbox;
};

// Sizes interface
type ThemeSizes = {
  mainContentWidth: string;
  cardContentMaxWidth: number;
};

// Main global theme interface
export type GlobalTheme = {
  breakpoints: ThemeBreakpoints;
  font: ThemeFont;
  layout: ThemeLayout;
  palette: ThemePalette;
  space: ThemeSpace;
  heightRule: ThemeHeightRules;
  border: ThemeBorder;
  radius: ThemeRadius;
  component: ThemeComponent;
  sizes: ThemeSizes;
};

const themeBreakpoints: ThemeBreakpoints = {
  xss: 360,
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
};

const themeFont: ThemeFont = {
  family: 'Be Vietnam Pro',
  weight: {
    light: 300,
    regular: 400,
    medium: 500,
    semiBold: 600,
    bold: 700,
  },
  size: {
    base: '14px',
    lg: '16px',
    sm: '12px',
  },
};

const themeLayout: ThemeLayout = {
  main: {
    header: {
      height: 84,
    },
    sidebar: {
      width: 270,
      collapsedWidth: 100,
    },
  },
};

const primaryColor = '#796CFF';

const themePalette: ThemePalette = {
  common: {
    black: '#000',
    white: '#FFF',
  },
  primary: primaryColor,
  primaryActive: lighten(0.2, primaryColor),
  primaryHover: lighten(0.25, primaryColor),
  primaryActiveHover: lighten(0.18, primaryColor),
  secondary: '#b242f4',
  success: '#67AA49',
  error: '#CF2A27',
  warning: '#EC9B13',
  info: '#2B78E4',
  infoText: '#2B78E4',
  infoBorder: '#2B78E4',
  infoBg: '#e6f4ff',
  text: {
    primary: '#3A3A3A',
    secondary: '#898989',
    content: 'rgb(41, 41, 41)',
    dark: '#333333',
    light: '#C3C3C3',
    heading: '#000000',
    subheading: '#565656',
  },
  background: {
    default: '#FFF',
    paper: '#FFF',
    component: '#F7F7F7',
    header: '#FFF',
    colorPrimaryBg: '#f4f0ff',
    disabled: '#F7F7F7',
  },
};

const themeSpace: ThemeSpace = {
  xl: '32px',
  lg: '24px',
  md: '16px',
  sm: '12px',
  xs: '8px',
  xss: '4px',
};

const themeHeightRules: ThemeHeightRules = {
  base: '32px',
  lg: '40px',
  sm: '24px',
};

const themeBorder: ThemeBorder = {
  color: '#DBDBDB',
  style: 'solid',
  width: '1px',
};

const themeRadius: ThemeRadius = {
  base: 12,
  sm: 10,
  circle: '50%',
  button: 0,
};

const themeComponent: ThemeComponent = {
  grid: {
    gutter: 24,
  },
  table: {
    headBackground: '#D3DAF8',
    rowHover: '#F2F4FD',
  },
  card: {
    boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.01)',
    borderRadius: `${themeRadius.base}px`,
    headerBgColor: '#F4F7FA',
  },
  tabs: {
    bgColor: '#F4F7FA',
    hoverBgColor: '#cbd7e3',
  },
  checkbox: {
    borderRadius: '4px',
  },
};

export const globalTheme: GlobalTheme = {
  breakpoints: themeBreakpoints,
  font: themeFont,
  layout: themeLayout,
  palette: themePalette,
  space: themeSpace,
  heightRule: themeHeightRules,
  border: themeBorder,
  radius: themeRadius,
  component: themeComponent,
  sizes: {
    mainContentWidth: '760px',
    cardContentMaxWidth: 760,
  },
};
