import type {
  Dispatch,
  MutableRefObject,
  ReactNode,
  SetStateAction,
} from 'react';
import type {
  UsePaginatedConnectorDataActions,
  UsePaginatedConnectorDataState,
  UsePaginatedDataActions,
  UsePaginatedDataState,
} from '../api-hooks';
import type { Call, CallItem } from '../calls';
import type { Conversation } from '../conversation';
import type { Document } from '../document';
import type { ConversationsHandle, NotesHandle } from '../handles';
import type { Spaces, SpaceSchema } from '../space';

export type PathData = {
  tab?: string;
  id?: string;
};

export type AppSpaceContextType = {
  notesRef: MutableRefObject<NotesHandle | null>;
  conversationsRef: MutableRefObject<ConversationsHandle | null>;
  token?: string;
  notesData: UsePaginatedDataState<Conversation[]>;
  callsData: UsePaginatedDataState<CallItem[]>;
  activeCall: Call | null;
  connectorData: UsePaginatedConnectorDataState<Document[]>;
  conversationData: UsePaginatedDataState<Conversation[]>;
  activeTab: string;
  activeDocument: Document | null;
  documentMode: string;
  currentSpace: Spaces | null;
  spaceSchema: SpaceSchema;
  activeConversation: Conversation | null;
  spaces: Spaces[];
  activeNote: Conversation | null;
  selectedDocs: unknown[];
  breadcrumb: unknown;
};

export type AppSpaceActionsContextType = {
  notesActions: UsePaginatedDataActions<Conversation[]>;
  connectorActions: UsePaginatedConnectorDataActions<Document[]>;
  callsActions: UsePaginatedDataActions<CallItem[]>;
  setActiveCall: Dispatch<SetStateAction<Call | null>>;
  conversationActions: UsePaginatedDataActions<Conversation[]>;
  setActiveTab: Dispatch<SetStateAction<string>>;
  setCurrentSpace: Dispatch<SetStateAction<Spaces | null>>;
  setSpaceSchema: Dispatch<SetStateAction<SpaceSchema>>;
  setActiveConversation: Dispatch<SetStateAction<Conversation | null>>;
  setActiveDocument: Dispatch<SetStateAction<Document | null>>;
  setDocumentMode: Dispatch<SetStateAction<string>>;
  setActiveNote: Dispatch<SetStateAction<Conversation | null>>;
  setSelectedDocs: Dispatch<SetStateAction<unknown[]>>;
  setSpaces: Dispatch<SetStateAction<Spaces[]>>;
  setBreadcrumb: Dispatch<SetStateAction<unknown>>;
  setPathData: Dispatch<SetStateAction<PathData>>;
};

export type AppSpaceContextProviderProps = {
  children: ReactNode;
  space?: Spaces;
  token?: string;
};
