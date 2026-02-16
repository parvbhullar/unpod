import styled from 'styled-components';

export const StyledRootContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 60px auto;
`;
