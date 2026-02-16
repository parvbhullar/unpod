import styled from 'styled-components';
import { Avatar, Typography } from 'antd';

// Reusable container for Contact form
export const StyledContactContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px;
  width: 600px;
  max-width: 100%;
  margin: 0 auto;
`;

// Header section
export const StyledContactHeader = styled.div`
  text-align: center;
`;

// Section title
export const StyledContactTitle = styled(Typography.Title)<{ $mb?: number }>`
  margin-bottom: ${({ $mb }) => $mb ?? 0}px !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 30px !important;
  }
`;

// Paragraph content
export const StyledContactContent = styled(Typography.Paragraph)`
  margin-bottom: 32px !important;
  font-size: 18px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-bottom: 26px !important;
    font-size: 16px;
  }
`;

// Optional avatar (use if needed)
export const StyledContactAvatar = styled(Avatar)`
  background-color: ${({ theme }) => theme.palette.error};
  margin-bottom: 24px;
`;

export const StyledCheckboxWrapper = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 16px;

  span {
    font-weight: 600;
    font-size: 16px;
  }
`;
