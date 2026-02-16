import styled from 'styled-components';
import { Row } from 'antd';

export const StyledDetailsRoot = styled.div`
  margin: 0;
`;
export const StyledRow = styled(Row)`
  padding: 16px;
  width: 100%;
`;

export const StyledSummaryContent = styled.div`
  margin: 16px 16px 0 16px;

  & .ant-collapse {
    background-color: ${({ theme }) => theme.palette.primaryHover};
  }

  & .ant-collapse-content {
    background-color: ${({ theme }) => theme.palette.primaryHover};
    font-size: 16px;
    line-height: 1.7;
  }

  p {
    margin: 0;
  }
`;
