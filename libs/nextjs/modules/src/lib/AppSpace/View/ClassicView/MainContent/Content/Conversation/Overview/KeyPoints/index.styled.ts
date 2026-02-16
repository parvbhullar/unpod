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

export const StyledAvatar = styled(Avatar)`
  background-color: ${({ theme }) => theme.palette.background.component};
  color: ${({ theme }) => theme.palette.text.secondary};
`;
