import styled from 'styled-components';
import {Space, Tag} from 'antd';

export const StyledListHeader = styled.div`
  display: flex;
  min-width: 0;
  align-items: flex-start;
  align-self: stretch;
  padding-block: 16px 8px;
  cursor: pointer;

  //position: sticky;
  //top: 0;
  background-color: ${({theme}) => theme.palette.background.default};
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

export const StyledWrapper = styled.div`
  display: none;

  &.expanded {
    display: block;
  }
`;

export const StyledContent = styled.div`
  margin: 0 0 10px 0;
  font-size: 15px;
  line-height: 1.7;

  & a {
    word-break: break-all;
  }
`;

export const StyledDetailsItems = styled.div`
  padding: 0 16px 16px 16px;
  border-block-end: 1px solid ${({theme}) => theme.border.color};
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

export const StyledTagItem = styled(Tag)`
  padding-block: 4px;
  text-transform: capitalize;
  border-radius: 10px;
  line-height: 1.5;
`;
