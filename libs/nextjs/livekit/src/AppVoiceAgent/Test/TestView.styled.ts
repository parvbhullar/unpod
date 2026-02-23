import styled, {keyframes} from 'styled-components';
import {Button} from 'antd';

export const WidgetContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  min-height: 100%;
  max-height: 100%;
  margin-bottom: 12px;
  width: 100%;
  bottom: 0;
  position: sticky;
`;

export const TopContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
`;

export const StyledAgentContainer = styled.div<{ direction: string }>`
  display: flex;
  flex-direction: ${({direction}) => direction};
  align-items: center;
  justify-content: center;
  margin-bottom: -20px;
  position: sticky;
  gap: 8px;
  bottom: -20px;
  padding: 0 1rem 1rem 1rem;
  width: 100%;
`;

export const wave = keyframes`
  0% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.7);
  }
  100% {
    transform: scaleY(1);
  }
`;

export const VoiceWave = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 28px;

  .bar {
    width: 4px;
    background: #555454;
    border-radius: 4px;
    animation: ${wave} 0.9s ease-in-out infinite;

    /* IMPORTANT */
    transform-origin: center;
  }

  /* RiVoiceprint style base shape */

  .bar:nth-child(1) {
    height: 8px;
    animation-delay: 0s;
  }

  .bar:nth-child(2) {
    height: 14px;
    animation-delay: 0.12s;
  }

  .bar:nth-child(3) {
    height: 20px;
    animation-delay: 0.24s;
  }

  .bar:nth-child(4) {
    height: 14px;
    animation-delay: 0.36s;
  }

  .bar:nth-child(5) {
    height: 8px;
    animation-delay: 0.48s;
  }
`;

export const FlexContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  width: 100%;
`;

export const StyledButton = styled(Button)`
  width: 100%;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
  border-radius: 12px !important;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  height: 51px !important;

  border: 1px solid red;
  background-color: transparent;
  color: red;

  &:hover {
    background-color: #edb0b6;
    color: red;
  }
`;
