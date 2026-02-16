import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  justify-content: space-between;
  width: 100%;
  // height: 100%;
  height: calc(100vh - 64px);
`;

export const StyledContainer = styled.div`
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  overflow: hidden;
`;

export const StyledFooterContainer = styled.div`
  flex-shrink: 0;
  width: 100%;
  height: 70px;
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: #fff;
  padding-inline: 12px;
`;
