import {tablePageSize} from '@unpod/constants';
import {AppRouterInstance} from 'next/dist/shared/lib/app-router-context.shared-runtime';
import type {Organization} from '@unpod/constants/types';

const pageLimit = tablePageSize * 2;

export type ListConfig = {
  url: string;
  params?: Array<{ key: string; value: string }>;
  getParams: (activeOrg: Organization | null) => Record<string, unknown>;
  callBack?: (
    data: unknown[],
    router: AppRouterInstance,
    pathname: string,
  ) => void;
};

export type APIDataConfig = {
  uniqueKey: string;
  path: string;
  list: ListConfig;
  get: string;
  create: string;
  update: string;
  delete: string;
};

export const APIData: Record<string, APIDataConfig> = {
  bridge: {
    uniqueKey: 'handle',
    path: '/ai-studio',
    list: {
      url: 'core/pilots/menus/',
      getParams: (activeOrg: Organization | null) => {
        return {
          page_size: pageLimit,
          domain: activeOrg?.domain_handle,
        };
      },
      callBack: (
        data: unknown[],
        router: AppRouterInstance,
        pathname: string,
      ) => {
        if (data.length > 0 && pathname === '/ai-studio/') {
          router.push(`/ai-studio/${(data[0] as { handle: string }).handle}/`);
        } else if (data.length === 0 && pathname === '/ai-studio/') {
          router.push(`/ai-studio/new/`);
        }
      },
    },
    get: '/api/studio/:id',
    create: '/api/studio',
    update: '/api/studio/:id',
    delete: '/api/studio/:id',
  },
  agent: {
    uniqueKey: 'handle',
    path: '/ai-studio',
    list: {
      url: 'core/pilots/menus/',
      getParams: (activeOrg: Organization | null) => {
        return {
          page_size: pageLimit,
          domain: activeOrg?.domain_handle,
        };
      },
      callBack: (
        data: unknown[],
        router: AppRouterInstance,
        pathname: string,
      ) => {
        if (data.length > 0 && pathname === '/ai-studio/') {
          router.push(`/ai-studio/${(data[0] as { handle: string }).handle}/`);
        } else if (data.length === 0 && pathname === '/ai-studio/') {
          router.push(`/ai-studio/new/`);
        }
      },
    },
    get: '/api/studio/:id',
    create: '/api/studio',
    update: '/api/studio/:id',
    delete: '/api/studio/:id',
  },
};
