import styled from 'styled-components';

export const StyledThreadContainer = styled.div`
  display: flex;
  position: relative;
  //border-radius: ${({theme}) => theme.component.card.borderRadius};
  overflow: hidden;
  // height: calc(100vh - 74px);
  gap: 5px;

  background-image: linear-gradient(
    90deg,
    rgba(138, 119, 255, 0.14) 50%,
    rgba(245, 136, 255, 0.14) 100%
  );
  background-color: rgba(245, 136, 255, 0.14);
`;

export const StyledLeftPanel = styled.div`
  border-left: 1px solid ${({theme}) => theme.border.color};
  position: relative;
  height: 100%;
`;

export const StyledRightPanel = styled(StyledLeftPanel)`
  background-color: ${({theme}) => theme.palette.background.default};
  overflow: hidden;
  flex: 1;
  //background-color: transparent;
`;
