import styled, { keyframes } from 'styled-components';
import { Tag, Typography } from 'antd';

const { CheckableTag } = Tag;
const { Paragraph } = Typography;

const scroll = keyframes`
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: calc(100vh - 152px);
  overflow-y: auto;
  max-width: 800px;
  margin: 0 auto;
`;

export const StyledTemplatesSection = styled.div`
  margin-top: 24px;
  margin-bottom: 24px;

  .templates-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    color: ${({ theme }) => theme.palette.text.primary};
  }
`;

export const StyledTemplatesScroll = styled.div`
  overflow-x: auto;
  position: relative;
  scrollbar-width: thin;

  &::-webkit-scrollbar {
    height: 6px;
  }

  &::-webkit-scrollbar-track {
    background: ${({ theme }) => theme.border.color};
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.border.color};
    border-radius: 3px;
  }

  &:hover .templates-track {
    animation-play-state: paused;
  }
`;

export const StyledTemplatesTrack = styled.div`
  display: flex;
  gap: 12px;
  width: max-content;
  animation: ${scroll} 20s linear infinite;
`;

export const StyledTemplateCard = styled.div<{ $selected?: boolean }>`
  flex: 0 0 auto;
  min-width: 200px;
  max-width: 240px;
  padding: 16px;
  border: 1px solid
    ${({ theme, $selected }) =>
      $selected ? theme.palette.primary : theme.border.color};
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  background: ${({ theme, $selected }) =>
    $selected
      ? `${theme.palette.primary}15`
      : theme.palette.background.default};
  transition: all 0.2s ease;
  ${({ $selected, theme }) =>
    $selected &&
    `
    box-shadow: 0 0 0 3px ${theme.palette.primary}30;
  `}

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .template-check {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: ${({ theme }) => theme.palette.primary};
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 12px;
  }

  .template-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    color: ${({ theme, $selected }) =>
      $selected ? theme.palette.primary : theme.palette.text.primary};
  }

  .template-description {
    font-size: 12px;
    color: ${({ theme }) => theme.palette.text.secondary};
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
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

  &.ant-tag-checkable-checked {
    border: 1px solid ${({ theme }) => theme.palette.primary};
    background: ${({ theme }) => theme.palette.background.default};
  }
`;

export const StyledSubtitle = styled(Paragraph)`
  overflow: hidden;
  width: 100%;
  word-wrap: break-word;
  white-space: normal;
  text-align: center;
  margin-bottom: 0 !important;
  font-size: 12px !important;
`;
