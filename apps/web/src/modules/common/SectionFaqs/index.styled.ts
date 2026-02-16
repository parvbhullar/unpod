import styled from 'styled-components';
import { Collapse } from 'antd';

export const StyledContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
`;

export const StyledCollapse = styled(Collapse)`
  border: none;
  background-color: transparent;

  & .ant-collapse-item {
    & .ant-collapse-header,
    & .ant-collapse-content-box {
      padding-inline: 0;
    }

    .ant-collapse-content-box {
      padding-block-start: 0;
    }

    & .ant-collapse-header-text {
      font-size: 16px;
      font-weight: 700;
      color: ${({ theme }) => theme.palette.text.primary};
    }

    & .ant-collapse-content {
      border: none;
      background-color: transparent;
    }
  }
`;
