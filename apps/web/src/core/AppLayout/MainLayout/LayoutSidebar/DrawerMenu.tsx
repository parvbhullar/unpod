import React from 'react';
import styled from 'styled-components';
import {
  useAppPageLayoutActionsContext,
  useAppPageLayoutContext,
} from '@/core/AppLayout/PageContentLayout/AppPageLayourContext';
import { MdOutlineMenu } from 'react-icons/md';

const IconWrapper = styled.span`
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
`;

const DrawerMenu = () => {
  const { isMobileView } = useAppPageLayoutContext();
  const { setInDrawerOpen } = useAppPageLayoutActionsContext();
  const { isDrawerOpened } = useAppPageLayoutContext();

  if (!isMobileView) {
    return null;
  }

  return (
    <IconWrapper onClick={() => setInDrawerOpen(!isDrawerOpened)}>
      <MdOutlineMenu />
    </IconWrapper>
  );
};

export default DrawerMenu;
