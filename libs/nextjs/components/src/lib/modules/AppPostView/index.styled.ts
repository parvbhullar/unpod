import styled from 'styled-components';
import { Tag, Typography } from 'antd';
import { GlobalTheme } from '@unpod/constants';

const { Text } = Typography;

export const StyledPostTitle = styled(Text)`
  font-size: 16px !important;
  margin-bottom: 0 !important;
  padding: 0;

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.md}px) {
    font-size: 14px !important;
  }

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    font-size: 12px !important;
  }
`;

export const StyledAvatarWrapper = styled.div`
  margin: 0;
  display: flex;
  align-items: center;
`;

export const StyledMeta = styled.div`
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: flex-start;
`;

export const StyledContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-bottom: 1px solid
    ${({ theme }: { theme: GlobalTheme }) => theme.border.color};
`;

export const StyledContentWrapper = styled.div`
  font-size: 16px;
  line-height: 1.6;
`;

export const StyledTitleRow = styled.div`
  display: flex;
  gap: 12px;
  padding: 0 20px;
  margin-bottom: 1em;

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    margin-bottom: 6px !important;
  }
`;

export const StyledTitleContainer = styled.div`
  max-width: calc(100% - 88px);

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    max-width: 100%;
  }
`;

export const StyledHeaderContainer = styled.div`
  max-width: calc(100% - 88px);
  margin-left: 44px;
  padding: 0 20px;
`;

export const StyledThumbnailsWrapper = styled.div`
  position: relative;
  width: 100%;
  padding-top: 33.3333%;
  border-radius: ${({ theme }: { theme: GlobalTheme }) => theme.radius.base}px;
  overflow: hidden;
  margin-bottom: 16px;
  cursor: pointer;
`;

export const StyledActionsWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  & .app-post-footer {
    opacity: 0;
    transition: opacity 0.2s ease-in;

    @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
        theme.breakpoints.md}px) {
      position: absolute;
      right: 0;
      background-color: ${({ theme }: { theme: GlobalTheme }) =>
        theme.palette.background.default};
      padding-inline-start: 5px;
    }
  }
`;

export const StyledContainer = styled.div`
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.background.default};
  transition: background-color 0.2s ease-in;
  max-width: calc(100% - 88px);
  padding: 0 20px;
  margin-left: 44px;

  &:hover ${StyledActionsWrapper}, &:hover .app-post-footer {
    opacity: 1;
  }

  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    padding: 0 10px;
    margin-left: 10px;
    max-width: 100%;
  }
`;

export const StyledTagItem = styled(Tag)`
  padding-block: 4px;
  text-transform: capitalize;
  border-radius: 10px;
  line-height: 1.5;
`;

export const StyledDetailsItems = styled.div`
  padding: 16px 0 0 0;
  transition: height 0.3s ease-in-out;
`;

export const StyledTimeText = styled(Text)`
  @media (max-width: ${({ theme }: { theme: GlobalTheme }) =>
      theme.breakpoints.sm}px) {
    font-size: 10px !important;
  }
`;
