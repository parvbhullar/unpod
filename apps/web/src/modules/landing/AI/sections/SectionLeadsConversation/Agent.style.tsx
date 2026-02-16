import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: 100%;
  margin: 0 auto;
  position: relative;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  padding: 16px 16px 12px 16px;
  overflow: hidden;
`;

export const CallButtonContainer = styled.div`
  position: relative;
  display: inline-block;
  z-index: 2;

  .call-button {
    //padding: 20px;
    font-weight: 600;
    //display: flex;
    //align-items: center;
    //gap: 8px;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
  }
`;

export const VoiceOverlay = styled.div<{ $show?: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  border-radius: 20px;
  opacity: ${(props) => (props.$show ? 1 : 0)};
  z-index: ${(props) => (props.$show ? 2000000 : 0)};
  transform: ${(props) => (props.$show ? 'scale(1)' : 'scale(0.5)')};
  transition:
    opacity 0.4s ease-in-out,
    transform 0.3s ease-in-out;
`;
