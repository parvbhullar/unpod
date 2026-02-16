'use client';
import styled from 'styled-components';
import { Tag } from 'antd';

const { CheckableTag } = Tag;

export const TagWrapper = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 52}px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
`;

export const TonePersonalityContainer = styled.div`
  margin-bottom: 12px;
`;

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
  justify-content: center;

  &.ant-tag-checkable-checked {
    border: 1px solid ${({ theme }) => theme.palette.primary};
    background: ${({ theme }) => theme.palette.background.default};
  }
`;
