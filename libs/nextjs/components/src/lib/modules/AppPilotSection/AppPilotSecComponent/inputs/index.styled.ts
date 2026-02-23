import styled from 'styled-components';
import {Slider, Typography} from 'antd';

const {Paragraph} = Typography;

export const StyledTitle = styled(Paragraph)`
  margin-bottom: 0 !important;
`;

export const StyledSlider = styled(Slider)`
  flex: 1;
  margin-right: 24px;

  .ant-slider-track {
    background-color: ${({theme}) => theme.palette.primary} !important;
  }

  .ant-slider-rail {
    background-color: #796cff33 !important;
  }

  .ant-slider-dot-active {
    border-color: ${({theme}) => theme.palette.primary} !important;
  }
`;

export const StyledRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
`;

export const StyledList = styled.div`
  display: flex;
  flex-direction: column;
  row-gap: 12px;
  padding: 12px;
  margin-bottom: 20px;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: 10px;

  @media screen and (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    row-gap: 24px;
  }
`;

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;
