import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    palette: {
      primary: string;
      secondary: string;
      primaryHover: string;
      primaryActive: string;
      text: {
        primary: string;
        secondary: string;
      };
      background: {
        default: string;
        component?: string;
      };
    };
    breakpoints: {
      xs: number;
      sm: number;
      md: number;
      lg: number;
      xl: number;
    };
  }
}
