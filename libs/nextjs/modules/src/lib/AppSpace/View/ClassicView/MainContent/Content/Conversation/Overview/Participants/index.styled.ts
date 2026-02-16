import styled from 'styled-components';
import { Avatar, Typography } from 'antd';

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

export const StyledText = styled(Text)`
  font-size: 13px;
`;

export const StyledDateText = styled(Text)`
  font-size: 13px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 10px !important;
  }
`;

export const StyledAvatar = styled(Avatar)<{ bgcolor?: string }>`
  background-color: ${({ theme, bgcolor }) =>
    bgcolor ? bgcolor : theme.palette.primary};
`;
