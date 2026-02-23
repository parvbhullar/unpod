'use client';
import SidebarHeader from './Header';
import {useAppSpaceContext} from '@unpod/providers';
import {StyledItemsWrapper, StyledRoot} from './index.styled';
import People from './People';
import Call from './Call';

const Sidebar = () => {
  const {activeTab} = useAppSpaceContext();

  return (
    <StyledRoot>
      <SidebarHeader/>
      <StyledItemsWrapper>
        {activeTab === 'doc' && <People/>}
        {activeTab === 'call' && <Call/>}
      </StyledItemsWrapper>
    </StyledRoot>
  );
};

export default Sidebar;
