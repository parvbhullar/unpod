import styled from 'styled-components';

export const StyledContainer = styled.div<{ $isScrolled?: boolean }>`
  margin: ${({ $isScrolled }) =>
    $isScrolled ? '16px auto 16px' : '16px auto 240px'};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  min-height: ${({ $isScrolled }) =>
    $isScrolled ? '50vh' : 'calc(100vh - 300px)'};
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition:
    min-height 0.8s,
    margin 0.8s;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
    min-height: ${({ $isScrolled }) =>
      $isScrolled ? '50vh' : 'calc(100vh - 184px)'};
  }
`;

export const StyledInfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 30px;
  text-align: center;

  & .ant-typography {
    margin: 0 !important;
  }
`;
