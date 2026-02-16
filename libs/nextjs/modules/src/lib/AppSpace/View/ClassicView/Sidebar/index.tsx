'use client';
import SidebarHeader from './Header';
import { useAppSpaceContext } from '@unpod/providers';
import Conversations from './Conversations';
import Notes from './Notes';
import { StyledItemsWrapper, StyledRoot } from './index.styled';
import People from './People';
import Call from './Call';
import type { ComponentType, Ref } from 'react';

const Sidebar = () => {
  const { activeTab, notesRef, conversationsRef } = useAppSpaceContext();
  const ConversationsComponent = Conversations as unknown as ComponentType<{
    ref?: Ref<unknown>;
  }>;
  const NotesComponent = Notes as unknown as ComponentType<{
    ref?: Ref<unknown>;
  }>;

  return (
    <StyledRoot>
      <SidebarHeader />
      <StyledItemsWrapper>
        {activeTab === 'chat' && (
          <ConversationsComponent ref={conversationsRef} />
        )}
        {activeTab === 'note' && <NotesComponent ref={notesRef} />}
        {activeTab === 'doc' && <People />}
        {activeTab === 'call' && <Call />}
      </StyledItemsWrapper>
    </StyledRoot>
  );
};

export default Sidebar;
