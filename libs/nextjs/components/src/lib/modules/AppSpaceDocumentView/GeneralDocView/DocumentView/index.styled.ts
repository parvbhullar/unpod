import styled from 'styled-components';
import { Space } from 'antd';

export const StyledListHeader = styled.div`
  display: flex;
  min-width: 0;
  align-items: flex-start;
  align-self: stretch;
  margin-bottom: 20px;
  //position: sticky;
  //top: 0;
  padding-block: 16px 8px;
  background-color: ${({ theme }) => theme.palette.background.default};
  z-index: 1;
`;

export const StyledMeta = styled.div`
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: flex-start;
`;

export const StyledAvatarWrapper = styled.div`
  margin: 0 8px 6px 0;

  * + * {
    margin-left: 6px;
  }
`;

export const StyledCollapsedMeta = styled.div`
  min-width: 0;
  padding-left: 2px;
  flex: 1;

  .item-title {
    margin-bottom: 0;
    font-size: 16px;
    font-weight: 500;
  }

  .item-user-name {
    margin-bottom: 0;
    padding-left: 1px;
    font-size: 13px;
  }
`;

export const StyledItem = styled.div`
  margin: 0 8px 6px 0;

  * + * {
    margin-left: 6px;
  }
`;

export const StyledHeaderExtra = styled(Space)`
  margin-left: 20px;
`;

export const StyledContent = styled.div`
  margin: 0 0 10px 0;
  font-size: 15px;
  line-height: 1.7;

  & a {
    word-break: break-all;
  }

  & p {
    word-break: break-word;
  }
`;

export const StyledDetailsItems = styled.div`
  padding: 0 16px 16px 16px;
  border-block-end: 1px solid ${({ theme }) => theme.border.color};
`;
