import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    breakpoints: {
      xss: number;
      xs: number;
      sm: number;
      md: number;
      lg: number;
      xl: number;
      xxl: number;
    };
    font: {
      family: string;
      weight: {
        light: number;
        regular: number;
        medium: number;
        semiBold: number;
        bold: number;
      };
      size: {
        base: string;
        lg: string;
        sm: string;
      };
    };
    layout: {
      main: {
        header: {
          height: number;
        };
        sidebar: {
          width: number;
          collapsedWidth: number;
        };
      };
    };
    palette: {
      common: {
        black: string;
        white: string;
      };
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
      text: {
        primary: string;
        secondary: string;
        content: string;
        dark: string;
        light: string;
        heading: string;
        subheading: string;
      };
      background: {
        default: string;
        paper: string;
        component: string;
        header: string;
        colorPrimaryBg: string;
        disabled: string;
      };
    };
    space: {
      xl: string;
      lg: string;
      md: string;
      sm: string;
      xs: string;
      xss: string;
    };
    heightRule: {
      base: string;
      lg: string;
      sm: string;
    };
    border: {
      color: string;
      style: string;
      width: string;
    };
    radius: {
      base: number;
      sm: number;
      circle: string;
      button: number;
    };
    component: {
      grid: {
        gutter: number;
      };
      table: {
        headBackground: string;
        rowHover: string;
      };
      card: {
        boxShadow: string;
        borderRadius: string;
        headerBgColor: string;
      };
      tabs: {
        bgColor: string;
        hoverBgColor: string;
      };
      checkbox: {
        borderRadius: string;
      };
    };
    sizes: {
      mainContentWidth: string;
      cardContentMaxWidth: number;
    };
  }
}

export type GlobalTheme = import('styled-components').DefaultTheme;
