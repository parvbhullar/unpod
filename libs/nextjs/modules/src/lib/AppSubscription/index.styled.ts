import styled from 'styled-components';
import { Card } from 'antd';

export const StyledRoot = styled.div`
  width: 100%;
  max-width: 1050px;
  margin: 16px auto;
  display: flex;
  gap: 14px;
  flex-direction: column;
  justify-content: space-between;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg + 140}px) {
    margin-block: 0;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-block: 0;
    padding: 5px;
  }
`;

export const StyledCard = styled(Card)`
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  background: ${({ theme }) => theme.palette.background.default};
  border: 1px solid #f0f0f0;
  height: 100%;
  display: flex !important;
  flex-direction: column !important;
  position: relative;

  .ant-card-head {
    border-bottom: none;
    padding: 20px 20px 0 20px;
    flex-shrink: 0;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 10px !important;
    }
  }

  div.ant-typography {
    white-space: normal !important;
    word-break: break-word;
    font-size: 14px;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .ant-card-body {
    padding: 10px 20px 20px 20px;
    font-size: 14px;
    display: flex;
    flex-direction: column;
    flex: 1;


    .row-inline {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
    }

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 5px 10px 10px 10px !important;
    }
`;

export const StyledButtonWrapper = styled.div`
  display: flex;
  align-items: center;
  height: 100%; /* ensures button stays vertically aligned */
`;

export const StyledSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
`;

export const StyledSectionLeft = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  margin-right: 8px;
`;
