import styled from 'styled-components';

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 32px;
  height: 32px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 10px;
  overflow: hidden;
`;

export const StyledTitle = styled.div`
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.035em;
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const StyledSubTitle = styled.div`
  font-size: 14px;
  color: ${({ theme }) => theme.palette.primary};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const StyledContent = styled.div`
  max-width: calc(100% - 56px);
`;

export const StyledActions = styled.div`
  position: absolute;
  display: flex;
  bottom: 0.75rem;
  right: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s ease-in;

  & .ant-btn {
    width: 24px;
    height: 24px;
    padding: 0;
    border-radius: 6px;
  }
`;

export const StyledPilotCard = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 16px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  cursor: pointer;
  display: flex;
  gap: 16px;
  height: 100%;
  position: relative;

  &:hover ${StyledActions} {
    opacity: 1;

    /*& .ant-btn {
      background: rgba(0, 0, 0, 0.6);
      color: ${({ theme }) => theme.palette.common.white};
    }*/
  }
`;
