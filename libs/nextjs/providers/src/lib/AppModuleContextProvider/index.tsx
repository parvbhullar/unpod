'use client';

import React, {
  createContext,
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useRef,
  useState,
} from 'react';
import { useAuthContext } from '../context-provider/AuthContextProvider';
import { usePaginatedDataApi } from '../APIHooks';
import { usePathname, useRouter } from 'next/navigation';
import { APIData } from './data';
import type { Organization } from '@unpod/constants/types';

export type ModuleRecord = {
  [key: string]: unknown;};

export type AppModuleContextType = {
  record: ModuleRecord | null;
  listData: unknown;
  isNewRecord: boolean;};

export type AppModuleActionsContextType = {
  setRecord: Dispatch<SetStateAction<ModuleRecord | null>>;
  listActions: unknown;
  setIsNewRecord: Dispatch<SetStateAction<boolean>>;
  deleteRecord: (slug: string) => void;
  updateRecord: (record: ModuleRecord) => void;
  refreshRecords: () => void;
  addNewRecord: (record: ModuleRecord) => void;};

const ContextState: AppModuleContextType = {
  record: null,
  listData: null,
  isNewRecord: false,
};

const AppModuleContext = createContext<AppModuleContextType>(ContextState);
const AppModuleActionsContext = createContext<
  AppModuleActionsContextType | undefined
>(undefined);

export const useAppModuleContext = (): AppModuleContextType =>
  useContext(AppModuleContext);
export const useAppModuleActionsContext = (): AppModuleActionsContextType => {
  const context = useContext(AppModuleActionsContext);
  if (!context) {
    throw new Error(
      'useAppModuleActionsContext must be used within AppModuleContextProvider',
    );
  }
  return context;
};

export type AppModuleContextProviderProps = {
  children: ReactNode;
  type?: 'bridge' | 'agent';};

export const AppModuleContextProvider: React.FC<
  AppModuleContextProviderProps
> = ({ children, type = 'bridge' }) => {
  const [record, setRecord] = useState<ModuleRecord | null>(null);
  const { activeOrg } = useAuthContext();
  const activeOrgRef = useRef<Organization | null>(activeOrg);
  const [isNewRecord, setIsNewRecord] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const [listData, listActions] = usePaginatedDataApi<ModuleRecord[]>(
    APIData[type].list.url,
    [],
    APIData[type].list.getParams(activeOrg),
    false,
    false,
    false,
    (data: ModuleRecord[]) => {
      if (APIData[type].list?.callBack) {
        if (activeOrgRef.current !== activeOrg) {
          activeOrgRef.current = activeOrg;
          if (data.length === 0) {
            router.replace(`${APIData[type].path}/new/`);
          } else {
            router.replace(
              `${APIData[type].path}/${(data[0] as Record<string, unknown>)[APIData[type].uniqueKey]}/`,
            );
          }
        } else {
          APIData[type].list?.callBack?.(data, router, pathname);
        }
      }
    },
  );

  const refreshRecords = (): void => {
    (
      listActions as {
        setPage: (p: number) => void;
        setQueryParams: (p: Record<string, unknown>) => void;
      }
    ).setPage(1);
    (
      listActions as {
        setPage: (p: number) => void;
        setQueryParams: (p: Record<string, unknown>) => void;
      }
    ).setQueryParams({ page: 1 });
  };

  const updateRecord = (updatedRecord: ModuleRecord): void => {
    (
      listActions as {
        setData: (fn: (prev: ModuleRecord[]) => ModuleRecord[]) => void;
      }
    ).setData((prevData: ModuleRecord[]) =>
      prevData.map((item) =>
        item[APIData[type].uniqueKey] === updatedRecord[APIData[type].uniqueKey]
          ? { ...item, ...updatedRecord }
          : item,
      ),
    );
  };

  const addNewRecord = (newRecord: ModuleRecord): void => {
    (
      listActions as {
        setData: (fn: (prev: ModuleRecord[]) => ModuleRecord[]) => void;
      }
    ).setData((prevData: ModuleRecord[]) => [newRecord, ...prevData]);
    setIsNewRecord(false);
  };

  const deleteRecord = (slug: string): void => {
    (
      listActions as {
        setData: (fn: (prev: ModuleRecord[]) => ModuleRecord[]) => void;
      }
    ).setData((prevData: ModuleRecord[]) =>
      prevData.filter((item) => item[APIData[type].uniqueKey] !== slug),
    );
    setRecord(null);
    setIsNewRecord(false);
  };

  return (
    <AppModuleActionsContext.Provider
      value={{
        setRecord,
        listActions,
        setIsNewRecord,
        deleteRecord,
        updateRecord,
        refreshRecords,
        addNewRecord,
      }}
    >
      <AppModuleContext.Provider
        value={{
          record,
          listData,
          isNewRecord,
        }}
      >
        {children}
      </AppModuleContext.Provider>
    </AppModuleActionsContext.Provider>
  );
};

export default AppModuleContextProvider;
