import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
`;

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  .ant-form-item {
    margin-bottom: 0;
  }
`;
