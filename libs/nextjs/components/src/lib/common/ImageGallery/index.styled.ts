import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: grid;
  grid-gap: 12px;
  /*display: flex;
  gap: 12px;
  flex-wrap: wrap;*/
  // width: 100%;
  min-height: 10px;
`;

export const StyledActionsWrapper = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  bottom: auto;
  right: auto;
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
  padding: 4px 8px;
  border-radius: 0 0 10px 0;

  & .download-btn {
    opacity: 0;
    color: ${({theme}) => theme.palette.background.default};
  }
`;

export const StyledGalleryItem = styled.div`
  cursor: pointer;
  position: relative;
  // min-height: 80px;
  min-width: 80px;
  max-width: 100%;
  display: inline-block;
  border: 1px solid ${({theme}) => theme.palette.primary}33;
  border-radius: 10px;
  overflow: hidden;

  & .gallery-thumbnail {
    height: 100%;
    min-height: 60px;
    max-width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &:hover {
    ${StyledActionsWrapper} {
      opacity: 1;

      & .download-btn {
        opacity: 1;
      }
    }
  }
`;
