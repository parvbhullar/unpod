import styled from 'styled-components';

export const StyledSuggestionRoot = styled.div`
  padding: 16px;
  position: sticky;
  bottom: 0;
  background-color: ${({theme}) => theme.palette.background.default};
  z-index: 1;
`;
export const StyledContainer = styled.div`
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
`;
