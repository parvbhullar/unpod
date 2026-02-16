import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledContainer = styled.div`
  margin-bottom: 24px;
`;

export const StyledTitleContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  top: 0;
  background-color: #fff;
  margin-bottom: 18px;
  margin-top: -12px;
  z-index: 1;

  & .ant-typography {
    margin: 0;
  }
`;

export const StyledSectionDivider = styled.div`
  width: 100%;
  height: 1px;
  background: #c6c5c5;
  margin: 40px 0;
`;

export const IconCircleGreen = styled.span`
  background: #eafaf3;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const IconCirclePurple = styled.span`
  background: #f6e7ff;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const StyledTitle = styled(Typography.Title)`
  && {
    font-weight: 700;
    margin-bottom: 0;
  }
`;

export const StyledSubtext = styled(Typography.Paragraph)`
  && {
    margin-top: 4px;
    margin-bottom: 0;
    color: #6b7280;
    font-size: 0.8rem;
    font-weight: 500;
  }
`;

export const StyledSmallSubtext = styled(Typography.Paragraph)`
  && {
    margin-top: 2px;
    margin-bottom: 0;
    color: #6b7280;
    font-size: 0.8rem;
    font-weight: 500;
  }
`;
export const StyledTextBlock = styled.div`
  display: flex;
  flex-direction: column;
`;
