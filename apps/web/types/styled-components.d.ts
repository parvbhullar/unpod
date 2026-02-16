import 'styled-components';

// Theme types - matching the GlobalTheme from libs/mix/src/lib/theme.ts
interface ThemeBreakpoints {
  xss: number;
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

interface ThemeFontWeight {
  light: number;
  regular: number;
  medium: number;
  semiBold: number;
  bold: number;
}

interface ThemeFontSize {
  base: string;
  lg: string;
  sm: string;
}

interface ThemeFont {
  family: string;
  weight: ThemeFontWeight;
  size: ThemeFontSize;
}

interface ThemeLayoutHeader {
  height: number;
}

interface ThemeLayoutSidebar {
  width: number;
  collapsedWidth: number;
}

interface ThemeLayoutMain {
  header: ThemeLayoutHeader;
  sidebar: ThemeLayoutSidebar;
}

interface ThemeLayout {
  main: ThemeLayoutMain;
}

interface ThemePaletteCommon {
  black: string;
  white: string;
}

interface ThemePaletteText {
  primary: string;
  secondary: string;
  content: string;
  dark: string;
  light: string;
  heading: string;
  subheading: string;
}

interface ThemePaletteBackground {
  default: string;
  paper: string;
  component: string;
  header: string;
  colorPrimaryBg: string;
  disabled: string;
}

interface ThemePalette {
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
}

interface ThemeSpace {
  xl: string;
  lg: string;
  md: string;
  sm: string;
  xs: string;
  xss: string;
}

interface ThemeHeightRules {
  base: string;
  lg: string;
  sm: string;
}

interface ThemeBorder {
  color: string;
  style: string;
  width: string;
}

interface ThemeRadius {
  base: number;
  sm: number;
  circle: string;
  button: number;
}

interface ThemeComponentGrid {
  gutter: number;
}

interface ThemeComponentTable {
  headBackground: string;
  rowHover: string;
}

interface ThemeComponentCard {
  boxShadow: string;
  borderRadius: string;
  headerBgColor: string;
}

interface ThemeComponentTabs {
  bgColor: string;
  hoverBgColor: string;
}

interface ThemeComponentCheckbox {
  borderRadius: string;
}

interface ThemeComponent {
  grid: ThemeComponentGrid;
  table: ThemeComponentTable;
  card: ThemeComponentCard;
  tabs: ThemeComponentTabs;
  checkbox: ThemeComponentCheckbox;
}

interface ThemeSizes {
  mainContentWidth: string;
  cardContentMaxWidth: number;
}

declare module 'styled-components' {
  export interface DefaultTheme {
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
  }
}
