import styled from 'styled-components';
import { Typography } from 'antd';
import { GlobalTheme } from '@unpod/constants';

export const StyledListItemMetaWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  // width: 436px;
  min-width: 200px;
  width: 100%;
`;

export const StyledCardWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  cursor: pointer;
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.background.default};
  border-radius: ${({ theme }: { theme: GlobalTheme }) =>
    theme.component.card.borderRadius};
  box-shadow: ${({ theme }: { theme: GlobalTheme }) =>
    theme.component.card.boxShadow};
`;
export const StyledCardContentWrapper = styled.div`
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
`;

export const StyledThreadMeta = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding-top: 10px;
`;
export const StyledTitleWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
`;
export const StyledMetaContent = styled.div`
  display: flex;
  min-width: 0;
  flex: 1;
  margin-top: 2px;
`;

export const StyledHubSpaceTitle = styled(Typography.Paragraph)`
  font-size: 14px;
  color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.primary};
  margin-bottom: 0 !important;

  .ant-typography {
    margin: 0;
  }
`;

export const StyledTitleItem = styled.div`
  width: calc(100% - 44px);
  .title {
    margin-bottom: 0;
    line-height: 1.2;
    font-size: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
  }
`;

export const StyledGridThumbnailWrapper = styled.div`
  position: relative;
  max-height: 202px;
  // min-height: 180px;
  overflow: hidden;
  display: flex;
  // opacity: 0.9;
  flex: 1;
  padding-top: 56.25%;
  border-radius: ${({ theme }: { theme: GlobalTheme }) =>
    theme.component.card.borderRadius};
`;
export const StyledContentWrapper = styled.div`
  margin-top: 8px;
  margin-bottom: 8px;
  overflow: hidden;
  color: #666666;
`;

export const StyledPlayWrapper = styled.div`
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
  color: #fff;
  cursor: pointer;
  background-color: rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  border-radius: 50%;
  padding: 8px;

  svg {
    margin-left: 2px;
    margin-right: -2px;
    font-size: 24px;
  }
`;
