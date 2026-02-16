import AppInfoViewProvider from '@unpod/providers/AppInfoViewProvider';
import AppContextProvider from '@unpod/providers/AppContextProvider';
import AppHistoryProvider from '@unpod/providers/AppHistoryProvider';
// import AppRouteProgressBar from '@unpod/components/AppRouteProgressBar';
import { AuthContextProvider, TourContextProvider } from '@unpod/providers';
import AppLocaleProvider from '@unpod/providers/AppLocaleProvider';
import AppThemeProvider from '@unpod/providers/AppThemeProvider';
import AppStyleProvider from '@unpod/providers/AppStyleProvider';
import { GlobalStyles } from '../../theme/GlobalStyle';
import { theme } from '../../theme';
import AppDndProvider from '@unpod/providers/AppDndProvider';
import { App } from 'antd';
import NextAuthWrapper from './NextAuthWrapper';
import type { LayoutProps } from '@/types/common';

const AppProviders = ({ children }: LayoutProps) => {
  return (
    <AppInfoViewProvider>
      <AppContextProvider>
        <AppThemeProvider theme={theme}>
          <App>
            <AppHistoryProvider>
              <AppDndProvider>
                {/*<AppRouteProgressBar/>*/}
                <NextAuthWrapper>
                  <AuthContextProvider>
                    <AppLocaleProvider>
                      <AppStyleProvider theme={theme}>
                        <GlobalStyles />
                        <TourContextProvider>{children}</TourContextProvider>
                      </AppStyleProvider>
                    </AppLocaleProvider>
                  </AuthContextProvider>
                </NextAuthWrapper>
              </AppDndProvider>
            </AppHistoryProvider>
          </App>
        </AppThemeProvider>
      </AppContextProvider>
    </AppInfoViewProvider>
  );
};

export default AppProviders;
