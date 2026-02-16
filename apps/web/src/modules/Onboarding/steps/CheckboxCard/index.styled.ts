'use client';
import styled from 'styled-components';
import { Tag, Typography } from 'antd';

const { CheckableTag } = Tag;

const { Text } = Typography;

export const StyledCheckableTag = styled(CheckableTag)`
  display: flex;
  flex-direction: column;
  margin: 0;
  align-items: center;
  padding: 16px 16px;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid ${({ theme }) => theme.palette.text.light};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow} !important;
  background: ${({ theme }) => theme.palette.background.default};
  color: ${({ theme }) => theme.palette.text.primary};
  transition: all 0.2s ease;
  white-space: normal;
  text-align: center;

  &.ant-tag-checkable-checked {
    border: 1px solid ${({ theme }) => theme.palette.primary};
    background: ${({ theme }) => theme.palette.background.default};
  }
`;

export const StyledSubtitle = styled(Text)`
  overflow: hidden;
  width: 100%;
  word-wrap: break-word;
  white-space: normal;
  text-align: center;
  margin-bottom: 0 !important;
`;

export const StyledCardIcon = styled.div`
  margin-bottom: 8px;
`;
