import styled from 'styled-components';

export const StyledContainer = styled.div`
  padding: 4px;

  .ant-descriptions-item-label {
    padding: 16px 20px !important;
    width: 60% !important;
    white-space: normal !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 30% !important;
      padding: 8px 8px !important;
    }
  }

  .ant-descriptions-item-content {
    padding: 16px 20px !important;
    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 8px 8px !important;
      white-space: normal !important;
      word-break: break-word;
    }
  }
`;
