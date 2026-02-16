import styled from 'styled-components';

export const StyledIconWrapper = styled.div`
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: 16px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

export const StyledCardRoot = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  // align-items: flex-start;
  gap: 16px;
  padding: 24px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border: 1px solid transparent;
  border-radius: 16px;
  cursor: pointer;
  max-width: 100%;
  height: 100%;
  transition: border-color 0.3s ease;

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
  }
`;

export const StyledCardContent = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 16px;

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
`;

export const StyledAppInfo = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  position: relative;

  & > .app-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;

    span {
      font-weight: 600;
      font-size: 16px;
      flex: 1;
    }

    .gear {
      color: ${({ theme }) => theme.palette.text.secondary};
      cursor: pointer;
      position: absolute;
      right: 0;
      top: -8px;
      transition: color 0.3s ease;

      &:hover {
        color: ${({ theme }) => theme.palette.text.primary};
      }
    }

    @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
      justify-content: center;
      position: static;

      span {
        font-size: 14px;
      }

      .gear {
        position: static;
        margin-left: 8px;
      }
    }
  }

  & > div:last-child {
    font-size: 13px;
    color: ${({ theme }) => theme.palette.text.secondary};
    margin-top: 4px;

    @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
      font-size: 12px;
    }
  }
`;

export const StyledConnectedChannelsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  align-items: center;
  gap: 16px;
`;

export const StyledConnectedBadge = styled.span`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  border-radius: 25px;
  padding: 9px 24px;
  font-size: 14px;
  font-weight: 500;
  align-self: flex-start;
  display: inline-block;
`;

export const StyledSectionWrapper = styled.div`
  margin-bottom: 24px;
`;

export const StyledAddMoreRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: ${({ theme }) => theme.palette.common.white};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 12px;
  margin-bottom: 16px;
  width: 100%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
  }
`;

export const StyledAddMoreRowContent = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  & > div {
    display: flex;
    flex-direction: column;
    justify-content: center;

    & > span:first-child {
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 8px;
    }

    & > span:last-child {
      font-weight: normal;
      font-size: 14px;
      color: ${({ theme }) => theme.palette.text.secondary};
      line-height: 1.4;
    }
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    width: 100%;

    & > div {
      & > span:first-child {
        font-size: 14px;
        margin-bottom: 4px;
      }

      & > span:last-child {
        font-size: 13px;
      }
    }
  }
`;
