import styled from 'styled-components';

export const StyledParent = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;

  .ant-typography {
    margin-bottom: 0;
    flex: 1;
  }
`;

export const StyledTooltipContent = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
`;
