import styled from 'styled-components';
import { Avatar } from 'antd';

export const StyledIconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  background-color: ${({ theme }) => theme.palette.primary}33;
  border: 1px solid ${({ theme }) => theme.palette.primary}77;
  border-radius: 12px;
  color: ${({ theme }) => theme.palette.primary}99 !important;
`;

export const StyledAvatar = styled(Avatar)`
  border: 1px solid ${({ theme }) => theme.palette.primary}99;
`;
