import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledFPContainer = styled.div`
  position: relative;
  height: 100%;
  // width: 37.5rem;
  max-width: 80%;
  overflow: hidden;
  margin: 0 auto;
  border-radius: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
    max-width: unset;
  }
`;

export const StyledFPInnerContainer = styled.div`
  display: flex;
  align-content: center;
  flex-direction: column;
  position: absolute;
  top: 40%;
  left: 0;
  width: 100%;
  text-align: center;
  overflow: hidden;
`;

export const StyledFPTitle = styled(Typography.Title)`
  font-size: 2.5rem !important;
`;

export const StyledFPSubTitle = styled(Typography.Paragraph)`
  font-size: 1.5rem !important;
`;
