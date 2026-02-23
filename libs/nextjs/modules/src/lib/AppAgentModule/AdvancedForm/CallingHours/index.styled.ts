import styled from 'styled-components';

import {Button} from 'antd';

export const StyledContainer = styled.div``;

export const StyledDaysContainer = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    gap: 6px;
  }
`;

export const StyledDayButton = styled(Button)`
  min-width: 64px;
  height: 32px;
  padding: 4px 15px;
  border-radius: 6px;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}) {
    width: 100%;
  }
`;

export const StyledTimeRangesWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 0 0 -24px 0;
  align-items: flex-start;
`;

export const StyledTimeRangeRow = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;

  .ant-picker {
    width: 100%;
    max-width: 150px;
  }
`;

export const StyledDeleteButton = styled(Button)`
  border: none;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  svg {
    color: #ff4d4f;
  }
  &:hover svg {
    color: #ff7875;
  }
`;

export const StyledAddRangeLink = styled(Button)`
  color: ${({theme}) => theme.palette.primary};
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    color: ${({theme}) => theme.palette.primaryHover};
  }
`;
