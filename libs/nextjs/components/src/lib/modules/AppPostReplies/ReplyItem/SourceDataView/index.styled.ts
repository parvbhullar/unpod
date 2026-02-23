import styled from 'styled-components';
import {Typography} from 'antd';

const {Title, Paragraph} = Typography;

export const StyledRootContainer = styled.div`
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

export const StyledDocContainer = styled.div`
  display: flex;
  flex-direction: column;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: ${({theme}) => theme.radius.base}px;
  background-color: ${({theme}) => theme.palette.background.default};
  padding: 16px;
  transition:
    background-color 0.2s ease-in-out,
    border-color 0.2s ease-in-out;

  &.highlight {
    border-color: ${({theme}) => theme.palette.primaryActive};
    background-color: ${({theme}) => theme.palette.background.component};
  }

  &:hover {
    background-color: ${({theme}) => theme.palette.background.component};
  }
`;

export const StyledTitle = styled(Title)`
  font-weight: 500 !important;
`;

export const StyledHighlight = styled(Paragraph)`
  font-size: 16px;
`;

export const StyledListContainer = styled.div`
  display: flex;
  flex-direction: column;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: ${({theme}) => theme.radius.base}px;
  overflow: hidden;
`;

export const StyledListItem = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid ${({theme}) => theme.border.color};
  background-color: ${({theme}) => theme.palette.background.default};
  transition: background-color 0.2s ease;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background-color: ${({theme}) => theme.palette.background.component};
  }
`;

export const StyledLabel = styled(Paragraph)`
  font-weight: 600;
  padding: 10px;
  text-transform: capitalize;
  margin-bottom: 0 !important;
  border-right: 1px solid ${({theme}) => theme.border.color};
  display: flex;
  align-items: center;
`;

export const StyledContent = styled(Paragraph)`
  padding: 0 10px;
  margin: 10px 0 !important;
`;

export const StyledZoomContainer = styled(Paragraph)`
  position: absolute;
  right: 0;
  bottom: 0;
  padding: 2px 4px;
  background: ${({theme}) => theme.palette.background.component};
  border-radius: 10px;
  margin-bottom: 0 !important;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s ease;
`;

export const StyledCellContent = styled.div`
  position: relative;

  &:hover ${StyledZoomContainer} {
    opacity: 1;
  }

  & a.ant-typography {
    color: ${({theme}) => theme.palette.primary};
  }
`;

export const StyledCopyWrapper = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
  z-index: 1;
  opacity: 0;
  background: ${({theme}) => theme.palette.background.component};
  border-radius: ${({theme}) => theme.radius.circle};
  transition: opacity 0.3s;
`;

export const StyledFullContent = styled(StyledRootContainer)`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${({theme}) => theme.palette.background.default};
  opacity: 0;
  transform: scale(0);
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;

  &.open {
    transform: scale(1);
    opacity: 1;
  }

  &.closing {
    transform: scale(0);
    opacity: 0;
  }

  &:not(.ref-content):hover ${StyledCopyWrapper} {
    opacity: 1;
  }
`;

export const StyledContentContainer = styled.div`
  padding: 16px;
  height: 100%;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: ${({theme}) => theme.radius.base}px;
  position: relative;
  overflow: hidden;

  &.json-content {
    background: ${({theme}) => theme.palette.background.component};
  }

  & pre {
    overflow: visible;
  }
`;

export const StyledTitleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
`;

export const StyledContentWrapper = styled.div`
  overflow-y: auto;
  height: 100%;

  /*font-family: ${({theme}) => theme.font.family};
  font-size: 16px;
  line-height: 1.6;
  color: ${({theme}) => theme.palette.text.content};

  & ol,
  & ul,
  & dl {
    margin: 0;
    padding: 0 0 12px 20px;
  }*/
`;

export const StyledRefRow = styled.div`
  position: relative;

  &.json-content {
    background: ${({theme}) => theme.palette.background.component};
  }

  &:hover ${StyledCopyWrapper} {
    opacity: 1;
  }
`;

export const StyledDocWrapper = styled.div`
  overflow-y: auto;
  height: 100%;
  //display: flex;
  //flex-direction: column;
  //gap: 20px;
`;

export const StyledIframeContainer = styled.div`
  // flex: 1;
  height: 100%;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: ${({theme}) => theme.radius.base}px;
  overflow: hidden;
`;
