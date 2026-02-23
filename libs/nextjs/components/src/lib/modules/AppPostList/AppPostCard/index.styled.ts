import styled from 'styled-components';
import {Typography} from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  // align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  min-width: 0;
  cursor: pointer;
  padding: 16px;
  // border-bottom: 1px solid ${({theme}) => theme.border.color};
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
`;

export const StyledMeta = styled(Typography.Paragraph)`
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 210px;
  max-width: 100%;
  flex: 1;
  margin-bottom: 0 !important;
  padding: 0 4px;
`;

export const StyledMetaContent = styled.div`
  display: flex;
  min-width: 0;
  flex: 1;
  margin-bottom: 5px;
`;

export const StyledItem = styled.div`
  margin: 0 8px 0 0;
  cursor: pointer;

  * + * {
    margin-left: 6px;
  }

  .font-weight-medium {
    font-weight: 500;
  }
`;

export const StyledHubSpaceTitle = styled(Typography.Paragraph)`
  font-size: 14px;
  color: ${({theme}) => theme.palette.primary};
  margin-bottom: 0 !important;

  .ant-typography {
    margin: 0;
  }
`;

export const StyledPostMedia = styled.div`
  display: flex;
  flex-direction: column;
  // margin-left: 20px;
`;

export const StyledThumbnailWrapper = styled.div`
  position: relative;
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  max-width: 260px;
  min-width: 210px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 62.25%;
  // flex: 1;
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
