import styled from 'styled-components';

export const WidgetContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  background: white;
  min-height: 100%;
  max-height: 100%;
  //padding: 1rem;
  width: 100%;
  bottom: 0;
  position: sticky;
`;


export const CenteredContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 70px);
`;

export const TopContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
`;

export const StyledAgentContainer = styled.div`
  display: flex;
  flex-direction: ${({ direction }) => direction};
  align-items: center;
  margin-bottom: -20px;
  position: sticky;
  gap: 8px;
  bottom: -20px;
  padding: 0 1rem 1rem 1rem;
`;

export const StyledVisualizerContainer = styled.div`
  display: flex;
  flex-direction: row;
  height: auto;
  width: 100%;
  color: #333333;
  align-items: center;
  justify-content: center;
  // border: ${({ theme }) => `1px solid ${theme?.palette.text.primary}`};
  --lk-va-bar-width: 10px;
  --lk-va-bar-gap: 5px;
  --lk-fg: ${({ theme }) => theme?.palette.secondary};
`;

