import styled from 'styled-components';
import { GlobalTheme } from '@unpod/constants';

export const StyledRoot = styled.div`
  /*display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));*/
  display: flex;
  text-align: center;
  justify-content: center;
  // flex-direction: column;
  gap: 12px;
  padding: 24px;
  //max-width: 360px;
  //max-width: 128px;
  margin: 0 auto;
`;

export const StyledConnector = styled.div`
  display: flex;
  text-align: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  // background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.primary}33;
  border: 1px solid
    ${({ theme }: { theme: GlobalTheme }) => theme.palette.primaryActive};
  border-radius: 16px;
  padding: 12px 8px 8px 8px;
  transition: background-color 0.3s ease;
  cursor: pointer;
  height: 80px;
  width: 80px;

  &:hover {
    background-color: ${({ theme }: { theme: GlobalTheme }) =>
      theme.palette.primaryHover};
  }
`;

export const StyledConnectorProfile = styled.div`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  // padding: 4px 8px;
  font-size: ${({ theme }: { theme: GlobalTheme }) => theme.font.size.lg};
  font-weight: ${({ theme }: { theme: GlobalTheme }) =>
    theme.font.weight.medium};
`;
