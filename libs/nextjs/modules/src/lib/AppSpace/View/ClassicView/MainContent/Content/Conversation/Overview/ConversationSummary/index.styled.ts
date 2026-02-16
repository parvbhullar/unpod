import { Button, Card, Input, Typography } from 'antd';
import styled from 'styled-components';

const { Text } = Typography;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  height: calc(100vh - 180px);
  overflow-y: auto;

  /* @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 12px !important;
  } */

  /* @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    padding: 6px 8px 6px;
  } */
`;

export const StyledDateSection = styled.div`
  margin-bottom: ${({ theme }) => theme.space.lg};
  display: flex;
  flex-direction: column;
`;

export const StyledDateHeader = styled(Text)`
  font-size: 11px;
  color: ${({ theme }) => theme.palette.text.light};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: ${({ theme }) => theme.space.xss} !important;
`;

export const StyledEditButton = styled(Button)`
  position: absolute;
  top: ${({ theme }) => theme.space.md};
  right: ${({ theme }) => theme.space.md};
  padding: 6px 12px;
  border-radius: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  height: 28px !important;
  transition: all 0.2s;

  &:hover {
    background: ${({ theme }) => theme.palette.background.paper};
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    border-radius: ${({ theme }) => theme.radius.base + 8}px;
    right: 0;
    top: 0;
    padding: 4px 6px !important;
    transform: translate(25%, -25%);
  }
`;

export const StyledSecoundryButton = styled(Button)`
  padding: 6px ${({ theme }) => theme.space.sm};
  border-radius: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  color: ${({ theme }) => theme.palette.text.secondary};
  height: 28px !important;
  transition: all 0.2s;

  &:hover {
    background: ${({ theme }) => theme.palette.background.paper};
  }
`;

export const StyledPrimaryButton = styled(Button)`
  padding: 6px ${({ theme }) => theme.space.sm};
  border-radius: ${({ theme }) => theme.space.xs};
  font-size: ${({ theme }) => theme.font.size.sm};
  height: 28px !important;
  transition: all 0.2s;

  &:hover {
    background: ${({ theme }) => theme.palette.background.paper};
  }
`;
export const StyledHashText = styled.div`
  margin-top: 8px;
  font-weight: 600;
  font-size: 13px !important;
`;

export const StyledTextWrapper = styled.div`
  font-size: 13px;
  white-space: pre-wrap;
`;

export const StyledCard = styled(Card)`
  background-color: ${({ theme }) => theme.palette.background.component};
  border: 1px solid ${({ theme }) => theme.border.color};

  .ant-card-body {
    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 12px !important;
    }
  }
`;

export const StyledTextArea = styled(Input.TextArea)`
  width: 100%;
  border: none;
  background: transparent !important;
  line-height: 1.5 !important;
  font-size: 13px;
  min-height: 380px;
  border-radius: 0 !important;
  border-bottom: 1px solid ${({ theme }) => theme.border.color} !important;
  margin-bottom: ${({ theme }) => theme.space.sm};
  scrollbar-width: thin;

  &:focus {
    box-shadow: none;
  }
`;

export const StyledContent = styled.div`
  margin-top: 10px;
  font-size: 16px;
  line-height: 1.5;
`;
