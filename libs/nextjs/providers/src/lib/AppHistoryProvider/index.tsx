'use client';

import React, {createContext, Dispatch, ReactNode, SetStateAction, useContext, useMemo, useState,} from 'react';

export type HistoryContextType = {
  redirectTo: string | null;
  historyOrg: unknown;
  historySpace: unknown;
  nextStep: string | null;
  historyData: unknown;
};

export type HistoryActionsContextType = {
  setRedirectTo: Dispatch<SetStateAction<string | null>>;
  setHistoryOrg: Dispatch<SetStateAction<unknown>>;
  setHistorySpace: Dispatch<SetStateAction<unknown>>;
  setNextStep: Dispatch<SetStateAction<string | null>>;
  setHistoryData: Dispatch<SetStateAction<unknown>>;
};

const HistoryActionsContext = createContext<
  HistoryActionsContextType | undefined
>(undefined);
const HistoryContext = createContext<HistoryContextType | undefined>(undefined);

export const useAppHistory = (): HistoryContextType => {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error('useAppHistory must be used within AppHistoryProvider');
  }
  return context;
};

export const useAppHistoryActions = (): HistoryActionsContextType => {
  const context = useContext(HistoryActionsContext);
  if (!context) {
    throw new Error(
      'useAppHistoryActions must be used within AppHistoryProvider',
    );
  }
  return context;
};

export type AppHistoryProviderProps = {
  children: ReactNode;
};

const AppHistoryProvider: React.FC<AppHistoryProviderProps> = ({
                                                                 children,
                                                               }) => {
  const [redirectTo, setRedirectTo] = useState<string | null>(null);
  const [historyOrg, setHistoryOrg] = useState<unknown>(null);
  const [historySpace, setHistorySpace] = useState<unknown>(null);
  const [nextStep, setNextStep] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<unknown>(null);

  const actions = useMemo<HistoryActionsContextType>(() => {
    return {
      setRedirectTo,
      setHistoryOrg,
      setHistorySpace,
      setNextStep,
      setHistoryData,
    };
  }, []);

  const values = useMemo<HistoryContextType>(() => {
    return {
      redirectTo,
      historyOrg,
      historySpace,
      nextStep,
      historyData,
    };
  }, [redirectTo, historyOrg, historySpace, nextStep, historyData]);

  return (
    <HistoryActionsContext.Provider value={actions}>
      <HistoryContext.Provider value={values}>
        {children}
      </HistoryContext.Provider>
    </HistoryActionsContext.Provider>
  );
};

export default AppHistoryProvider;
