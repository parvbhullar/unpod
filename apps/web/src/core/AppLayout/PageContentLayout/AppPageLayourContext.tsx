'use client';
import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { useMediaQuery } from 'react-responsive';
import type { LayoutProps } from '@/types/common';

type AppPageLayoutState = {
  isDrawerOpened: boolean;
  sidebarWidth?: number;
  isMobileView: boolean;
};

type AppPageLayoutActions = {
  setInDrawerOpen: (open: boolean) => void;
};

const AppPageLayoutContext = createContext<AppPageLayoutState>({
  isDrawerOpened: false,
  isMobileView: false,
  sidebarWidth: undefined,
});
const AppPageLayoutActionsContext = createContext<AppPageLayoutActions | null>(
  null,
);

export const useAppPageLayoutContext = () => useContext(AppPageLayoutContext);
export const useAppPageLayoutActionsContext = () => {
  const context = useContext(AppPageLayoutActionsContext);
  if (!context) {
    throw new Error(
      'useAppPageLayoutActionsContext must be used within AppPageLayoutContextProvider',
    );
  }
  return context;
};

export const AppPageLayoutContextProvider = ({
  children,
  sidebarWidth,
  drawerOpenBreakpoint = 768,
}: LayoutProps & { sidebarWidth?: number; drawerOpenBreakpoint?: number }) => {
  const [isDrawerOpened, setInDrawerOpen] = useState(false);
  const pathname = usePathname();
  const pathNameRef = useRef(pathname);

  const isMobileView = useMediaQuery({
    query: `(max-width: ${drawerOpenBreakpoint}px)`,
  });

  useEffect(() => {
    if (pathNameRef.current !== pathname) setInDrawerOpen(false);
  }, [pathname]);

  return (
    <AppPageLayoutActionsContext.Provider value={{ setInDrawerOpen }}>
      <AppPageLayoutContext.Provider
        value={{ isDrawerOpened, sidebarWidth, isMobileView }}
      >
        {children}
      </AppPageLayoutContext.Provider>
    </AppPageLayoutActionsContext.Provider>
  );
};

export default AppPageLayoutContextProvider;
