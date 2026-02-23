'use client';

import type {
  AppSpaceActionsContextType,
  AppSpaceContextProviderProps,
  AppSpaceContextType,
  Call,
  CallItem,
  Conversation,
  ConversationsHandle,
  Document,
  PathData,
  Spaces,
  SpaceSchema,
  UsePaginatedConnectorDataState,
  UsePaginatedDataState,
} from '@unpod/constants/types';

import React, {createContext, useContext, useEffect, useRef, useState,} from 'react';
import {useParams, usePathname, useRouter} from 'next/navigation';

import {POST_TYPE} from '@unpod/constants/AppEnums';

import {getDataApi, usePaginatedConnectorDataApi, usePaginatedDataApi,} from '../../APIHooks';
import {useAuthActionsContext, useAuthContext} from '../AuthContextProvider';
import {useInfoViewActionsContext} from '../AppInfoViewProvider';
import {useOrgContext} from '../AppOrgContextProvider';

const emptyConversationDataState: UsePaginatedDataState<Conversation[]> = {
  loading: false,
  apiData: [],
  extraData: {},
  page: 1,
  queryParams: {},
  isLoadingMore: false,
  refreshing: false,
  initialUrl: '',
  hasMoreRecord: false,
};

const emptyCallsDataState: UsePaginatedDataState<CallItem[]> = {
  loading: false,
  apiData: [],
  extraData: {},
  page: 1,
  queryParams: {},
  isLoadingMore: false,
  refreshing: false,
  initialUrl: '',
  hasMoreRecord: false,
};

const emptyConnectorDataState: UsePaginatedConnectorDataState<Document[]> = {
  loading: false,
  apiData: [],
  page: 1,
  count: 0,
  isLoadingMore: false,
  refreshing: false,
  initialUrl: '',
  hasMoreRecord: false,
};

const ContextState: AppSpaceContextType = {
  conversationsRef: {current: null},
  token: undefined,
  notesData: emptyConversationDataState,
  callsData: emptyCallsDataState,
  activeCall: null,
  connectorData: emptyConnectorDataState,
  conversationData: emptyConversationDataState,
  activeTab: 'chat',
  activeDocument: null,
  documentMode: 'view',
  currentSpace: null,
  spaceSchema: {},
  activeConversation: null,
  spaces: [],
  activeNote: null,
  selectedDocs: [],
  breadcrumb: null,
};

const AppSpaceContext = createContext<AppSpaceContextType>(ContextState);
const AppSpaceActionsContext = createContext<
  AppSpaceActionsContextType | undefined
>(undefined);

export const useAppSpaceContext = (): AppSpaceContextType =>
  useContext(AppSpaceContext);
export const useAppSpaceActionsContext = (): AppSpaceActionsContextType => {
  const context = useContext(AppSpaceActionsContext);
  if (!context) {
    throw new Error(
      'useAppSpaceActionsContext must be used within AppSpaceContextProvider',
    );
  }
  return context;
};

const getActiveTab = (): string | null => {
  const pathname = usePathname();
  const params = useParams();

  if (!pathname || !params?.spaceSlug) return null;
  const parts = pathname.split('/').filter(Boolean);
  const idx = parts.indexOf(params.spaceSlug as string);
  return idx >= 0 && parts.length > idx + 1 ? parts[idx + 1] : null;
};

export const AppSpaceContextProvider: React.FC<
  AppSpaceContextProviderProps
> = ({children, space, token}) => {
  const tab = getActiveTab();
  const [documentMode, setDocumentMode] = useState('view');
  const [activeTab, setActiveTab] = useState(tab || 'chat');
  const [currentSpace, setCurrentSpace] = useState<Spaces | null>(
    space || null,
  );
  const [activeDocument, setActiveDocument] = useState<Document | null>(null);
  const [breadcrumb, setBreadcrumb] = useState<unknown>(null);
  const [spaceSchema, setSpaceSchema] = useState<SpaceSchema>({});
  const [activeConversation, setActiveConversation] =
    useState<Conversation | null>(null);
  const [spaces, setSpaces] = useState<Spaces[]>([]);
  const [activeNote, setActiveNote] = useState<Conversation | null>(null);
  const [activeCall, setActiveCall] = useState<Call | null>(null);
  const [selectedDocs, setSelectedDocs] = useState<unknown[]>([]);
  const {isAuthenticated, activeOrg, user} = useAuthContext();
  const {updateAuthUser} = useAuthActionsContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const conversationsRef = useRef<ConversationsHandle | null>(null);
  const currentIdRef = useRef<string | undefined>(undefined);
  const [pathData, setPathData] = useState<PathData>({
    tab: undefined,
    id: undefined,
  });
  const activeOrgRef = useRef(activeOrg?.domain_handle || null);
  const {notificationData} = useOrgContext();

  useEffect(() => {
    if (
      notificationData?.object_type === 'space' &&
      notificationData?.event_data?.slug === currentSpace?.slug
    ) {
      getDataApi<Spaces>(
        `spaces/${currentSpace?.slug}/`,
        infoViewActionsContext,
        {},
      ).then((response) => {
        setCurrentSpace(response.data);
        updateAuthUser({
          ...user,
          active_space: response.data,
        });
      });
    }
  }, [notificationData]);

  useEffect(() => {
    if (pathData.tab) {
      setActiveTab(pathData.tab);
      if (pathData.tab && pathData.id && currentIdRef.current !== pathData.id) {
        currentIdRef.current = pathData.id;
        if (pathData.tab === 'doc') {
          if (!activeDocument || activeDocument?.document_id !== pathData.id)
            getDataApi<Document>(
              `knowledge_base/${currentSpace?.token}/connector-doc-data/${pathData.id}/`,
              infoViewActionsContext,
            )
              .then((data) => {
                setActiveDocument(data.data);
              })
              .catch((error: { message: string }) => {
                infoViewActionsContext.showError(error.message);
              });
        } else if (pathData.tab === 'call') {
          if (!activeDocument || activeDocument?.document_id !== pathData.id)
            getDataApi<Call>(
              `spaces/${currentSpace?.slug}/calls/${pathData.id}/`,
              infoViewActionsContext,
            )
              .then((data) => {
                setActiveCall(data.data);
              })
              .catch((error: { message: string }) => {
                infoViewActionsContext.showError(error.message);
              });
        } else if (pathData.tab === 'chat' || pathData.tab === 'note') {
          if (pathData.tab === 'chat') setActiveConversation(null);
          else if (pathData.tab === 'note') setActiveNote(null);

          if (pathData.tab === 'chat') {
            getDataApi<Conversation>(
              `threads/${pathData.id}/detail/`,
              infoViewActionsContext,
            )
              .then((response) => {
                setActiveConversation(response.data);
              })
              .catch((error: { message: string }) => {
                infoViewActionsContext.showError(error.message);
              });
          } else if (pathData.tab === 'note') {
            getDataApi<Conversation>(
              `threads/${pathData.id}/detail/`,
              infoViewActionsContext,
            )
              .then((response) => {
                setActiveNote(response.data);
              })
              .catch((error: { message: string }) => {
                infoViewActionsContext.showError(error.message);
              });
          }
        }
      }
    }
  }, [pathData.id]);

  useEffect(() => {
    if (!activeOrgRef.current) {
      activeOrgRef.current = activeOrg?.domain_handle || null;
    } else if (
      activeOrgRef.current &&
      activeOrgRef.current !== activeOrg?.domain_handle
    ) {
      activeOrgRef.current = activeOrg?.domain_handle || null;
      router.push('/spaces/');
    }
  }, [activeOrg, router]);

  const [notesData, notesActions] = usePaginatedDataApi<Conversation[]>(
    `threads/${currentSpace?.token}/`,
    [],
    {
      post_type: POST_TYPE.POST,
    },
    false,
  );

  const [conversationData, conversationActions] = usePaginatedDataApi<
    Conversation[]
  >(
    `threads/${currentSpace?.token}/`,
    [],
    {
      post_type: `${POST_TYPE.ASK},${POST_TYPE.TASK},${POST_TYPE.QUESTION}`,
    },
    false,
  );

  const [callsData, callsActions] = usePaginatedDataApi<CallItem[]>(
    `spaces/${currentSpace?.slug}/calls/`,
    [],
    {
      page_size: 50,
    },
    false,
    false,
    false,
  );

  const [connectorData, connectorActions] = usePaginatedConnectorDataApi<
    Document[]
  >(
    `knowledge_base/${currentSpace?.token}/connector-data/`,
    [],
    {
      page_size: 50,
    },
    false,
    (schema: unknown) => setSpaceSchema(schema as SpaceSchema),
  );

  useEffect(() => {
    if (space?.token) {
      setSelectedDocs([]);
      setActiveDocument(null);
      setActiveConversation(null);
      setActiveNote(null);
      updateAuthUser({
        ...user,
        active_space: space,
      });
    }
    setCurrentSpace(space || null);
  }, [space?.token]);

  useEffect(() => {
    if (currentSpace?.token && isAuthenticated) {
      connectorActions.setPage(1);
      connectorActions.setQueryParams({page: 1, search: ''});

      connectorActions.updateInitialUrl(
        `knowledge_base/${currentSpace.token}/connector-data/`,
      );
    }
  }, [currentSpace?.token, isAuthenticated]);

  return (
    <AppSpaceActionsContext.Provider
      value={{
        notesActions,
        connectorActions,
        callsActions,
        setActiveCall,
        conversationActions,
        setActiveTab,
        setCurrentSpace,
        setSpaceSchema,
        setActiveConversation,
        setActiveDocument,
        setDocumentMode,
        setActiveNote,
        setSelectedDocs,
        setSpaces,
        setBreadcrumb,
        setPathData,
      }}
    >
      <AppSpaceContext.Provider
        value={{
          conversationsRef,
          token,
          notesData,
          callsData,
          activeCall,
          connectorData,
          conversationData,
          activeTab,
          activeDocument,
          documentMode,
          currentSpace,
          spaceSchema,
          activeConversation,
          spaces,
          activeNote,
          selectedDocs,
          breadcrumb,
        }}
      >
        {children}
      </AppSpaceContext.Provider>
    </AppSpaceActionsContext.Provider>
  );
};

export default AppSpaceContextProvider;
