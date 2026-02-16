import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
`;

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;
