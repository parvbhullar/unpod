import styled from 'styled-components';
import { Button, Card, Flex, Typography } from 'antd';

const { Text } = Typography;

export const StyledCard = styled(Card)`
  .ant-card-body {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 24px;
    align-items: center;
    width: 90%;
    margin: 0 auto;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 100%;
    }
  }
`;

export const StyledOTPContainer = styled.div`
  display: flex;
  justify-content: center;
  width: 100%;

  .ant-otp-input {
    border-radius: 6px !important;
  }

  .ant-otp {
    gap: 44px !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      gap: 6px !important;
    }
  }
`;

export const StyledEmailText = styled(Text)`
  color: ${({ theme }) => theme.palette.primary};
`;

export const StyledButton = styled(Button)`
  &.active {
    border-color: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.primary};
  }
`;

export const StyledEmailContainer = styled.div`
  display: flex;
  align-items: center;
  width: 100%;
  flex: 1 !important;
  flex-direction: column;

  .ant-form-item-explain-error {
    display: flex;
    justify-content: flex-start;
  }
`;

export const StyledAction = styled(Flex)`
  align-items: center;
  gap: 8px;
  justify-content: center;
  width: 100%;
`;

export const StyledActionWrapper = styled(Flex)`
  align-items: center;
  gap: 8px;
  justify-content: center;
  width: 100%;
  margin-bottom: 24px !important;
`;

export const StyledActionIcon = styled.span`
  display: flex;
  justify-content: center;
  cursor: pointer;
  color: ${({ theme }) => theme.palette.success};
  padding: 5px;
  border-radius: ${({ theme }) => theme.radius.base}px;
  background: ${({ theme }) => theme.palette.background.default};

  &.close-btn {
    color: ${({ theme }) => theme.palette.error};
  }

  &.edit-btn {
    color: ${({ theme }) => theme.palette.primary};
  }

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.component};
  }

  @media (max-width: 480px) {
    padding: 3px;
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100%;

  .ant-form-item-explain-error {
    margin-top: 10px;
    display: flex;
    justify-content: flex-start;
  }
`;
