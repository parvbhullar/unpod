import styled from 'styled-components';

export const StyledLogo = styled.div`
  font-weight: bold;
  font-size: 20px;
  color: ${({ theme }) => theme.palette.primary};
  padding: 14px;
  line-height: 0 !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 108px;
    padding: 0;
  }
`;
export const StyledHeader = styled.div`
  position: sticky;
  border-bottom: 1px solid ${({ theme }) => theme.border.color};
  gap: 20px;
  top: 0;
  background: ${({ theme }) => theme.palette.background.paper};
  z-index: 100;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 14px;
    align-items: center;
    text-align: center;
  }
`;
