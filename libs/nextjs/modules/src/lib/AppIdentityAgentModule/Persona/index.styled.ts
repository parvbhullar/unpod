import styled from 'styled-components';
import {Typography} from 'antd';

const {Paragraph} = Typography;

export const StyledSelectLabel = styled(Paragraph)`
  margin-bottom: 2px !important;
`;

export const StyledSelectDesc = styled(Paragraph)`
  margin-bottom: 0 !important;
  font-size: 12px;
`;

export const StyledSelectWrapper = styled.div`
  & .rc-virtual-list-holder-inner {
    gap: 3px;

    & .ant-select-item-option-selected ${StyledSelectDesc} {
      font-weight: normal;
    }
  }
`;
export const StyledMainContainer = styled.div`
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    width: 100%;
  }
`;
