import styled from 'styled-components';
import {PlaygroundTile} from '../../components/playground/PlaygroundTile';

const headerHeight = 56;
export const Container = styled.div`
  padding: 8px;
  height: calc(100% - ${headerHeight}px);

  align-items: center;
`;

export const AudioTileContainer = styled.div`
  display: flex;
  height: 40px;
  color: #333333;
  width: 100%;
`;
export const StyledPlaygroundTile = styled(PlaygroundTile)`
  height: 100%;
  flex-grow: 1;
  display: flex;
`;
export const FlexColumnCenter = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #4b5563;
  text-align: center;
`;

export const StyledAgentContainer = styled.div<{
  $direction?: string;
  $spaceView?: boolean;
}>`
  height: 40px;
  width: 180px;
  display: flex;
  flex-direction: ${({$direction}) => $direction || 'row'};
  align-items: center;
  align-content: center;
  justify-content: center;
  gap: ${({$spaceView}) => ($spaceView ? '8px' : '24px')};

  @media (max-width: ${({theme}) => theme?.breakpoints?.sm ?? 640}px) {
    gap: 6px !important;
  }
  @media (max-width: ${({theme}) => theme?.breakpoints?.xs ?? 480}px) {
    gap: 0 !important;
  }
`;

export const StyledVisualizerContainer = styled.div<{ $spaceView?: boolean }>`
  display: flex;
  flex-direction: row;
  height: auto;
  // width: 100%;
  color: #333333;
  align-items: center;
  // border: ${({theme}) => `1px solid ${theme?.palette?.text?.primary}`};
  justify-content: center;
  --lk-va-bar-width: ${({$spaceView}) => ($spaceView ? '6px' : '10px')};
  --lk-va-bar-gap: ${({$spaceView}) => ($spaceView ? '4px' : '5px')};
  --lk-fg: ${({theme}) => theme?.palette?.secondary};

  margin-left: 0;

  @media (max-width: ${({theme}) => theme?.breakpoints?.sm ?? 640}px) {
    --lk-va-bar-width: 8px;
    margin-left: 13px !important;
  }

  @media (max-width: ${({theme}) => theme?.breakpoints?.xs ?? 480}px) {
    --lk-va-bar-width: 6px;
    --lk-va-bar-gap: 4px;
    //margin-left: 13px !important;
  }
`;
