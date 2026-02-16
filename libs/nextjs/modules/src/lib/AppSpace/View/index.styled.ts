import styled from 'styled-components';
import { Typography } from 'antd';

const { Title } = Typography;

export const StyledContainer = styled.div`
  margin: 16px auto 40px auto;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
  }
`;

export const StyledPageContainer = styled.div`
  //display: flex;
  //flex-direction: column;
  // overflow: auto;
  //padding: 5px;
  width: 100%;
  max-width: calc(100vw - 72px);
  height: 100%;
  flex: 1;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    max-width: calc(100vw - 60px);
    flex-direction: row;
  }
`;

export const StyledNoAccessContainer = styled.div`
  margin: 16px auto;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
`;

export const StyledNoAccessText = styled(Title)`
  text-align: center;
`;
