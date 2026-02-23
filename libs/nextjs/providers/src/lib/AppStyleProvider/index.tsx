'use client';

import React, {ReactNode} from 'react';
import {DefaultTheme, ThemeProvider} from 'styled-components';

export type AppStyleProviderProps = {
  theme: DefaultTheme;
  children: ReactNode;
};

export const AppStyleProvider: React.FC<AppStyleProviderProps> = ({
                                                                    theme,
                                                                    children,
                                                                  }) => {
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

export default AppStyleProvider;
