import styled from 'styled-components';
import {Row, Typography} from 'antd';
import SimpleBar from 'simplebar-react';

const {Title} = Typography;

export const StyledRow = styled(Row)`
  padding: 16px;
  min-height: 80%;
`;

export const StyledRoot = styled.div`
  flex: 1;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
`;

export const StyledConversationItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  cursor: pointer;
  margin-bottom: 2px;
  transition: background 0.2s;

  &:hover {
    background-color: ${({theme}) => theme.palette.primaryHover};
  }

  &.active {
    background-color: ${({theme}) => theme.palette.primaryHover};
  }
`;

export const StyledItem = styled.div`
  flex-shrink: 0;

  & .ant-avatar-string {
    font-size: 12px;
  }
`;

export const StyledContent = styled.div`
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;

  & .ant-typography {
    margin: 0 !important;
  }
`;

export const StyledListHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  //align-self: stretch;
  justify-content: space-between;

  & .title-text {
    flex: 1;
  }
`;

export const StyledContainer = styled.div`
  flex: 1;
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 16px auto 16px;
  //padding-inline: 16px;
  display: flex;
  flex-direction: column;
  gap: 40px;

  @media (max-width: ${({theme}) => theme.breakpoints.lg + 200}px) {
    width: 500px;
  }
`;

export const StyledScrollbar = styled(SimpleBar)`
  height: calc(100vh - 64px);

  & .simplebar-content {
    min-height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
  }
`;

export const StyledList = styled.div`
  display: flex;
  flex-direction: column;
  //gap: 16px;
`;

export const StyledAskContainer = styled.div`
  min-height: 30vh;
  margin: 16px auto 16px;
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition:
    min-height 0.8s,
    margin 0.8s;

  &.content-center {
    min-height: 80%;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    width: 400px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    width: ${({theme}) => theme.sizes.mainContentWidth};
  }
`;

export const StyledInfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 30px;
  text-align: center;

  & .ant-typography {
    margin: 0 !important;
  }
`;

export const StyledTitle = styled(Title)`
  font-size: 14px !important;
  font-weight: 600 !important;
  color: ${({theme}) => theme.palette.common.black};
  margin: 0 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px !important;
`;

export const StyledConversationHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 3px;
`;

export const StyledConversationTime = styled.span`
  font-size: 11px;
  color: ${({theme}) => theme.palette.text.secondary};
  white-space: nowrap;
  margin-left: 8px;
`;
