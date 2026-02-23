import styled from 'styled-components';
import {Typography} from 'antd';

const {Paragraph} = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  cursor: pointer;
  padding: 16px;
  border-block-end: 1px solid ${({theme}) => theme.border.color};

  &:hover {
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  }

  &.active,
  &.selected {
    background-color: ${({theme}) => theme.palette.primaryHover};
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  }
`;

export const StyledListHeader = styled.div`
  display: flex;
  min-width: 0;
  align-items: flex-start;
  align-self: stretch;
  margin-bottom: 2px;
`;

export const StyledMeta = styled(Paragraph)`
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: flex-start;
  margin-bottom: 0 !important;
`;

export const StyledMetaContent = styled.div`
  display: flex;
  min-width: 0;
  flex: 1;
  // flex-wrap: wrap;
  margin-top: 5px;
  margin-left: 2px;
`;

export const StyledItem = styled.div`
  margin: 0 8px 6px 0;

  * + * {
    margin-left: 6px;
  }
`;

export const StyledHeaderExtra = styled.div`
  display: flex;
  align-items: center;
  margin-left: 20px;
`;

export const StyledContent = styled.div`
  display: flex;
  min-width: 0;
  align-items: center;
  align-self: stretch;
  margin-bottom: 5px;
`;

export const StyledContentDetails = styled.div`
  flex: 1;
  max-width: 100%;
`;
