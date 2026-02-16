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

export type AppModuleContextType<T> = {
  record: T | null;
  listData: unknown;
  isNewRecord: boolean;};

export type AppModuleActionsContextType<T> = {
  setRecord: Dispatch<SetStateAction<T | null>>;
  listActions: unknown;
  setIsNewRecord: Dispatch<SetStateAction<boolean>>;
  deleteRecord: (slug: string) => void;
  updateRecord: (record: T) => void;
  refreshRecords: () => void;
  addNewRecord: (record: T) => void;};

const ContextState: AppModuleContextType<Record<string, unknown>> = {
  record: null,
  listData: null,
  isNewRecord: false,
};

const AppModuleContext = createContext<AppModuleContextType<Record<string, unknown>>>(ContextState);
const AppModuleActionsContext = createContext<
  AppModuleActionsContextType<Record<string, unknown>> | undefined
>(undefined);

export const useAppModuleContext = <
  T,
>(): AppModuleContextType<T> =>
  useContext(AppModuleContext) as AppModuleContextType<T>;
export const useAppModuleActionsContext = <
  T,
>(): AppModuleActionsContextType<T> => {
  const context = useContext(AppModuleActionsContext);
  if (!context) {
    throw new Error(
      'useAppModuleActionsContext must be used within AppModuleContextProvider',
    );
  }
  return context as AppModuleActionsContextType<T>;
};

export type AppModuleContextProviderProps = {
  children: ReactNode;
  type?: 'bridge' | 'agent';};

export const AppModuleContextProvider: React.FC<
  AppModuleContextProviderProps
> = ({ children, type = 'bridge' }) => {
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const { activeOrg } = useAuthContext();
  const activeOrgRef = useRef<Organization | null>(activeOrg);
  const [isNewRecord, setIsNewRecord] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const [listData, listActions] = usePaginatedDataApi<Record<string, unknown>[]>(
    APIData[type].list.url,
    [],
    APIData[type].list.getParams(activeOrg),
    false,
    false,
    false,
    (data: Record<string, unknown>[]) => {
      if (APIData[type].list?.callBack) {
        if (activeOrgRef.current !== activeOrg) {
          activeOrgRef.current = activeOrg;
          if (data.length === 0) {
            router.replace(`${APIData[type].path}/new/`);
          } else {
            router.replace(
              `${APIData[type].path}/${data[0][APIData[type].uniqueKey]}/`,
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

  const updateRecord = (updatedRecord: Record<string, unknown>): void => {
    (
      listActions as {
        setData: (fn: (prev: Record<string, unknown>[]) => Record<string, unknown>[]) => void;
      }
    ).setData((prevData: Record<string, unknown>[]) =>
      prevData.map((item) =>
        item[APIData[type].uniqueKey] === updatedRecord[APIData[type].uniqueKey]
          ? { ...item, ...updatedRecord }
          : item,
      ),
    );
  };

  const addNewRecord = (newRecord: Record<string, unknown>): void => {
    (
      listActions as {
        setData: (fn: (prev: Record<string, unknown>[]) => Record<string, unknown>[]) => void;
      }
    ).setData((prevData: Record<string, unknown>[]) => [newRecord, ...prevData]);
    setIsNewRecord(false);
  };

  const deleteRecord = (slug: string): void => {
    (
      listActions as {
        setData: (fn: (prev: Record<string, unknown>[]) => Record<string, unknown>[]) => void;
      }
    ).setData((prevData: Record<string, unknown>[]) =>
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