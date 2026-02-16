import styled from 'styled-components';

export const StyledRoot = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;
