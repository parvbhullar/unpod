import styled from 'styled-components';

export const StyledRoot = styled.div`
  flex: 1;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius}
    ${({ theme }) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  padding: 24px;
`;

export const StyledCardContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr; /* Mobile screen pe ek hi column */
  }
`;
