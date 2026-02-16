import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  width: 100%;
  min-height: 10px;
`;

export const StyledActionsWrapper = styled.div`
  position: absolute;
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
  padding: 4px 8px;
  border-radius: 0 0 10px 0;

  & .download-btn {
    opacity: 0;
    color: ${({ theme }) => theme.palette.background.default};
  }
`;

export const StyledGalleryItem = styled.div`
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid ${({ theme }) => theme.palette.primary}33;
  cursor: pointer;
  position: relative;

  &:hover {
    ${StyledActionsWrapper} {
      opacity: 1;

      & .download-btn {
        opacity: 1;
      }
    }
  }
`;
