export type ConversationsHandle = {
  refreshData: () => void;
  addConversation: (newConversation: Record<string, unknown>) => void;
};

export type NotesHandle = {
  refreshData: () => void;
};
