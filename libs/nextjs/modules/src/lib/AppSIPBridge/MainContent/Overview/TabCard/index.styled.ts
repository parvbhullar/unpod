import styled from 'styled-components';
import { Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const StyledIconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 5px;
`;

export const StyledRoot = styled.div`
  padding: 32px 24px;
  height: 100% !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  text-align: center;
  cursor: pointer;

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
  }

  &.telephony ${StyledIconWrapper} {
    color: #7c3aed;
  }

  &.voice ${StyledIconWrapper} {
    color: ${({ theme }) => theme.palette.primary};
  }

  &.kyc ${StyledIconWrapper} {
    color: ${({ theme }) => theme.palette.success};
  }
`;

export const StyledTitle = styled(Title)`
  margin-bottom: 0 !important;
  white-space: nowrap;
`;

export const StyledDescription = styled(Paragraph)`
  font-size: 18px;
  margin-bottom: 0 !important;
`;
