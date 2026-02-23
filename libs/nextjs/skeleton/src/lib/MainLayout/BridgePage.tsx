'use client';
import React from 'react';
import styled from 'styled-components';
import {Divider} from 'antd';
import {SidebarAgentList} from '../SidebarAgentList';
import {BridgeStudioSkeleton} from '../BridgeStudio';
import SkeletonAvatar from '../common/SkeletonAvatar';
import {SkeletonInput} from '../common/SkeletonInput';
import {LayoutSidebarSkeleton} from './Sidebar';

const StyledSidebarContainer = styled.div`
  width: 320px;
  display: flex;
  flex-direction: column;
  border: 6px ${({theme}) => theme.border.style}
    ${({theme}) => theme.border.color};
  border-right-width: 3px;
  border-top-left-radius: ${({theme}) => theme.radius.base}px;
  border-top-right-radius: ${({theme}) => theme.radius.base}px;
  overflow: hidden;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    display: none;
  }
`;

const SidebarScroll = styled.div`
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
`;

const StyledBridgeContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 6px ${({theme}) => theme.border.style}
    ${({theme}) => theme.border.color};
  border-left-width: 3px;
  border-top-left-radius: ${({theme}) => theme.radius.base}px;
  border-top-right-radius: ${({theme}) => theme.radius.base}px;
  overflow: hidden;
`;

const BridgeScroll = styled.div`
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
`;

const BridgePageSkeleton: React.FC = () => {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        overflow: 'hidden',
      }}
    >
      <LayoutSidebarSkeleton/>
      <div style={{display: 'flex', flex: 1}}>
        <StyledSidebarContainer>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <SkeletonAvatar active size={32} shape="circle"/>
              <SkeletonInput active style={{width: 100, height: 20}}/>
            </div>
            <SkeletonAvatar active size={28} shape="circle"/>
          </div>

          <Divider style={{margin: 0}}/>

          <div style={{padding: '16px'}}>
            <SkeletonInput active style={{width: 280, height: 28}}/>
          </div>

          <SidebarScroll>
            <SidebarAgentList/>
          </SidebarScroll>
        </StyledSidebarContainer>

        <StyledBridgeContainer>
          <BridgeScroll>
            <BridgeStudioSkeleton/>
          </BridgeScroll>
        </StyledBridgeContainer>
      </div>
    </div>
  );
};

export {BridgePageSkeleton};
