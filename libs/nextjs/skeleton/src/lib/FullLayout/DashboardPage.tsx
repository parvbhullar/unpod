'use client';
import React from 'react';
import {DashboardSkeleton} from '../Dashboard';
import {LayoutSidebarSkeleton} from '../MainLayout/Sidebar';
import {HeaderSkeleton} from './Header';
import styled from 'styled-components';

const StyledContent = styled.div`
  flex: 1;
  border: 6px solid ${({theme}) => theme.border.color};
  border-top-left-radius: ${({theme}) => theme.component.card.borderRadius};
  border-top-right-radius: ${({theme}) => theme.component.card.borderRadius};
`;

const Dashboard: React.FC = () => {
  return (
    <div style={{display: 'flex', width: '100%', height: '100vh'}}>
      <LayoutSidebarSkeleton/>
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: '100vh',
          flexDirection: 'column',
        }}
      >
        <HeaderSkeleton/>
        <StyledContent>
          <DashboardSkeleton cards={3}/>
        </StyledContent>
      </div>
    </div>
  );
};

export {Dashboard};
