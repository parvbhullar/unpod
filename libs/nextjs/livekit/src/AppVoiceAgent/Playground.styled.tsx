import styled from 'styled-components';

export const StyledAgentContainer = styled.div<{ $direction?: string }>`
  display: flex;
  flex-direction: ${({ $direction }) => $direction || 'row'};
  align-items: center;
  justify-content: center;
  margin-bottom: -20px;
  position: sticky;
  gap: 8px;
  bottom: -20px;
  padding: 0 1rem 1rem 1rem;
  width: 100%;
`;

export const StyledVisualizerContainer = styled.div`
  display: flex;
  flex-direction: row;
  height: auto;
  width: 100%;
  color: #333333;
  align-items: center;
  justify-content: center;
  // border: ${({ theme }) => `1px solid ${theme?.palette?.text?.primary}`};
  --lk-va-bar-width: 10px;
  --lk-va-bar-gap: 5px;
  --lk-fg: ${({ theme }) => theme?.palette?.secondary};
`;
