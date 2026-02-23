import styled from 'styled-components';

export const StyledRoot = styled.div`
  flex: 1;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
`;

export const StyledContainer = styled.div`
  flex: 1;
  padding: 24px;
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  @media (max-width: 768px) {
    padding: 12px;
  }
`;
