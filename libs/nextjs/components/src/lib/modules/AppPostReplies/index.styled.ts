import styled from 'styled-components';
import {Button, Typography} from 'antd';
import AppList from '../../common/AppList';
import {GlobalTheme} from '@unpod/constants';

const {Link, Paragraph, Text} = Typography;

export const StyledRootContainer = styled.div`
  display: flex;
  flex-direction: column;
`;

export const StyledInnerContainer = styled.div`
  position: relative;
`;

export const StyledAppList = styled(AppList as any)`
  display: flex;
  flex-direction: column;
  gap: 0;
`;

export const StyledMoreContainer = styled.div`
  display: flex;
  justify-content: center;
  padding-top: 24px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    padding-top: 0;
  }
`;

export const StyledMsgChat = styled.div`
  display: flex;
  padding: 12px 20px;
  margin-top: 8px;
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  border-radius: ${({theme}: { theme: GlobalTheme }) => theme.radius.base}px;
  max-width: calc(100% - 128px);
  margin-left: 44px;
`;

export const StyledSystemMessage = styled.div`
  margin-top: 10px;
  border: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.palette.primary}55;
  border-radius: ${({theme}: { theme: GlobalTheme }) => theme.radius.base}px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
`;

export const StyledContainer = styled.div`
  margin: 24px 0 0;
  padding: 20px 10px 0 20px;
  border: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.palette.primary}55;
  border-radius: ${({theme}: { theme: GlobalTheme }) => theme.radius.base}px;

  .ant-timeline .ant-timeline-item {
    padding-bottom: 10px;
  }

  .ant-timeline .ant-timeline-item-head {
    transition: all 0.2s ease-in;
  }

  .ant-timeline-item-content {
    min-height: 0 !important;
  }

  .ant-timeline-item-last {
    padding-bottom: 0;
  }

  .ant-timeline-item-tail {
    border-color: #796cff40;
  }

  &:last-child {
    margin-bottom: 0;
  }
`;

export const StyledContent = styled.div`
  margin: 0;
  flex: 1;
  max-width: calc(100% - 150px);

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    max-width: 100% !important;
  }

  //border-bottom: 1px solid ${({theme}: { theme: GlobalTheme }) =>
  theme.border.color};
`;
export const StyledUserContent = styled.div`
  margin: 0;
  flex: 1;
  max-width: calc(100% - 88px);
  display: flex;
  flex-direction: column;
  gap: 4px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    max-width: 100%;

    display: flex;
    flex-direction: column;
    gap: 0 !important;
  }
  //border-bottom: 1px solid ${({theme}: { theme: GlobalTheme }) =>
  theme.border.color};
`;

export const StyledAvatar = styled.div`
  margin: 0;

  .user-question & {
    margin: 0;
  }
`;

export const StyledMeta = styled.div`
  text-align: justify;

  .app-post-viewer {
    max-width: none;
    padding: 10px 0 0;
  }
`;
export const StyledUserMeta = styled.div`
  text-align: justify;

  width: fit-content;
  margin-left: auto;

  background-color: rgba(152, 128, 255, 0.1);
  border-radius: ${({theme}: { theme: GlobalTheme }) => theme.radius.base}px;
  padding: 8px 12px;

  .app-post-viewer {
    max-width: none;
    padding: 10px 0 0;
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    padding: 2px 10px;
    border-radius: ${({theme}: { theme: GlobalTheme }) =>
  theme.radius.base - 6}px;
  }
`;

export const StyledMetaContent = styled.div`
  position: relative;
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 8px;
`;

export const StyledMetaTitle = styled.div`
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
`;

export const StyledTitle = styled(Link)`
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;

  &:hover {
    color: #3826f8 !important;
  }
`;

export const StyledTime = styled(Text)`
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    font-size: 10px;
    margin-left: 9px;
    margin-right: 15px;
  }
`;

export const StyledActions = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  justify-items: center;
  //justify-content: space-between;
  gap: 16px;

  & .app-post-footer {
    opacity: 0;
    transition: opacity 0.2s ease-in;
    align-items: center;
    text-align: center;

    @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.md}px) {
      position: absolute;
      bottom: 7px;
      right: 0;
      background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
      padding-inline-start: 5px;
    }

    @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
      flex: 1 !important;
      gap: 0 !important;
    }
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0;

    & .app-post-footer {
      opacity: 1 !important;
      position: static !important;
      background: none !important;
      padding: 0 !important;
      transition: none !important;
    }
  }
`;
export const StyledUserActions = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  text-align: center;
  gap: 16px;
  //height: 30px;

  & .app-post-footer {
    opacity: 0;
    transition: opacity 0.2s ease-in;
    align-items: center;
    text-align: center;

    @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.md}px) {
      position: absolute;
      bottom: 7px;
      right: 0;
      background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
      padding-inline-start: 5px;
    }
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-end;
    justify-content: flex-end;
    gap: 0;

    .app-post-footer {
      opacity: 1 !important;
      position: static !important;
      background: none !important;
      padding: 0 !important;
      transition: none !important;
    }
  }
`;

export const StyledReplyParent = styled.div`
  padding: 12px 12px 12px 12px;
  margin-bottom: 10px;
  cursor: pointer;
  position: relative;
  border-radius: 0 0 0 10px;
  box-shadow: -2px 2px 6px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease-in;
`;

export const StyledUserQuestion = styled(Text)`
  font-size: 14px;
  line-height: 1.6;
  color: ${({theme}: { theme: GlobalTheme }) => theme.palette.text.primary};

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    font-size: 12px;
  }
`;

export const StyledContentWrapper = styled.div`
  font-size: 14px;
  line-height: 1.6;

  &.system-message {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-block: 3px 16px;
    text-align: justify;
  }

  & .document-handle {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    color: ${({theme}: { theme: GlobalTheme }) => theme.palette.primary};
    background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.primaryHover};
    border-radius: 20px;
    font-size: 11px;
    margin-left: 2px;

    &:hover,
    &.active {
      text-decoration: underline;
      background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.primaryActive};
    }
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    font-size: 12px !important;
  }

  & p {
    text-align: justify;
  }
`;

export const StyledParent = styled(Paragraph)`
  display: flex;
  align-items: center;
  gap: 8px;

  .ant-typography {
    margin-bottom: 0;
    flex: 1;
  }
`;

export const StyledReplyContainer = styled.div`
  margin-bottom: 16px;
  position: relative;
  padding: 20px 20px 0 20px;
  display: flex;
  gap: 12px;

  /*&.user-question {
    border-bottom: none;
  }*/

  &:hover {
    ${StyledReplyParent} {
      background-color: transparent;
    }

    ${StyledActions}, .app-post-footer {
      opacity: 1;
    }

    .ant-timeline .ant-timeline-item-head {
      background-color: transparent;
    }
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    padding: 10px 20px 0 20px;
    flex-direction: column;
  }
`;

export const StyledUserContainer = styled.div`
  position: relative;
  padding: 20px 20px 0 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-left: 42px;

  /*&.user-question {
    border-bottom: none;
  }*/

  &:hover {
    ${StyledReplyParent} {
      background-color: transparent;
    }

    ${StyledActions}, .app-post-footer {
      opacity: 1;
    }

    .ant-timeline .ant-timeline-item-head {
      background-color: transparent;
    }
  }

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    padding: 10px 20px 0 20px;
    margin-left: 0;
  }
`;

export const StyledScrollBottom = styled.div`
  display: flex;
  justify-content: center;
  position: sticky;
  bottom: 150px;
  opacity: 1;
  height: auto;
  transition: all 0.2s ease-in;

  &.scrolled-to-bottom {
    opacity: 0;
    height: 0;
  }
`;

export const StyledNoteButton = styled(Button)`
  padding-inline: 10px !important;
  display: flex;
  align-items: center;
  gap: 6px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    height: 25px !important;
    font-size: 10px !important;
    padding: 6px 4px !important;
    gap: 2px !important;
  }
`;
