import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

export const StyledAttachment = styled.div`
  width: 82px;
  height: 80px;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid ${({ theme }) => theme.palette.primary}55;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  padding: 16px 12px 12px;
  cursor: pointer;
  position: relative;

  & .file-extension-name {
    white-space: nowrap;
    max-width: 100%;
    overflow: hidden;
    font-size: 12px;
  }

  &:hover .file-extension-name {
    color: rgba(0, 0, 0, 0.2) !important;
  }
`;

export const StyledActionsWrapper = styled.div`
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;

  & .download-btn {
    position: absolute;
    top: auto;
    bottom: auto;
    left: auto;
    right: auto;
    opacity: 0;
    color: ${({ theme }) => theme.palette.common.white};
  }

  &:hover {
    opacity: 1;

    & .download-btn {
      opacity: 1;
    }
  }
`;
