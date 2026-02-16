import { Button, Typography } from 'antd';
import styled from 'styled-components';

const { Text } = Typography;

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

export const StyledAudioPlayer = styled.div`
  padding: ${({ theme }) => theme.space.md};
  background: ${({ theme }) => theme.palette.background.paper};
  border-radius: 16px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
`;

export const StyledPlayButton = styled(Button)`
  background-color: ${({ theme }) => theme.palette.primary};
  border: none;
  border-radius: ${({ theme }) => theme.radius.circle};
  transition: background-color 0.2s;
  color: ${({ theme }) => theme.palette.common.white};

  &:hover,
  &:focus {
    background-color: ${({ theme }) => theme.palette.primaryHover} !important;
  }
`;

export const StyledAudioInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

export const StyledTimeDisplay = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: ${({ theme }) => theme.space.xs};
  font-size: 11px;
  color: ${({ theme }) => theme.palette.text.light};
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

export const StyledTextWrapper = styled.div`
  display: flex;
  alignitems: center;
  gap: 10px;
`;

export const StyledText = styled(Text)`
  font-size: 13px;
`;

export const StyledTimeText = styled(Text)`
  font-size: 11px;
  font-weight: ${({ theme }) => theme.font.weight.medium} !important;
`;
