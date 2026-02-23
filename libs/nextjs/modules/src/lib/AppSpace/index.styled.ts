import styled from 'styled-components';

export const StyledContainer = styled.div`
  flex: 1;
  padding: 2px 12px;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius};
`;
