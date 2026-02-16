import React from 'react';
import styled from 'styled-components';


export const TestsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  height: 100%;
`;

export const TestsContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: ${({ $startCall }) =>
    $startCall ? '115px' : 'calc(100vh - 260px)'};
  overflow-y: auto;
  scrollbar-width: none;
  padding-bottom: 12px;
`;

export const TestCard = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: ${({ theme }) =>
    theme.palette.background.component || '#1a1a1a'};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

export const TestInfo = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 2px;
`;

export const TestMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: ${({ theme }) => theme.palette.text.secondary || '#aaa'};
`;
