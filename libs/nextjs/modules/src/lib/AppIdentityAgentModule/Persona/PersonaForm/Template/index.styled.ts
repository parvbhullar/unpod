import styled from 'styled-components';
import {Tag, Typography} from 'antd';

const {CheckableTag} = Tag;
const {Paragraph} = Typography;

export const StyledTemplatesSection = styled.div`
  margin-top: 24px;
  margin-bottom: 24px;

  .templates-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    color: ${({theme}) => theme.palette.text.primary};
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
    background: ${({theme}) =>
  (theme as any)?.palette?.border?.secondary ||
  (theme as any)?.palette?.text?.light ||
  '#e5e7eb'};
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${({theme}) =>
  (theme as any)?.palette?.text?.secondary || '#bbb'};
    border-radius: 3px;
  }

  &:hover .templates-track {
    animation-play-state: paused;
  }
`;

export const StyledTemplatesTrack = styled.div`
  height: calc(100vh - 150px);
  overflow: auto;
  scrollbar-width: thin;
`;

export const StyledCheckableTag = styled(CheckableTag)`
  display: flex;
  flex-direction: column;
  margin: 0;
  align-items: center;
  padding: 16px 16px;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid ${({theme}) => theme.palette.text.light};
  box-shadow: ${({theme}) => theme.component.card.boxShadow} !important;
  background: ${({theme}) => theme.palette.background.default};
  color: ${({theme}) => theme.palette.text.primary};
  transition: all 0.2s ease;
  white-space: normal;
  text-align: center;

  &:hover {
    border: 1px solid ${({theme}) => theme.palette.primary};
    background: ${({theme}) => theme.palette.primaryHover} !important;
  }

  &.ant-tag-checkable-checked {
    border: 1px solid ${({theme}) => theme.palette.primary};
    background: ${({theme}) => theme.palette.background.default};
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
