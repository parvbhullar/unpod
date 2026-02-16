import styled from 'styled-components';
import { Flex } from 'antd';

export const StyledDetailsRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  height: calc(100vh - 74px);
  text-overflow: ellipsis;
`;

export const StyledFlexContainer = styled(Flex)`
  margin-top: 2px;
  width: 100%;
  align-items: center;
  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

export const StyledFlex = styled(Flex)`
  align-items: center;
  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

export const StyledFlexBadges = styled(Flex)`
  align-items: center;
  width: 100%;
  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    align-items: flex-start;
  }
`;
