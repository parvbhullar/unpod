import styled from 'styled-components';

export const StyledImageWrapper = styled.div`
  min-width: 50%;
  text-align: right;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    order: 1;
    text-align: center;
  }
`;

export const StyledTextContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-self: flex-end;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    text-align: center;
    order: 2;
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 60px;
  max-width: 1200px;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-direction: column;
  }

  &.reverse-position {
    ${StyledImageWrapper} {
      text-align: left;
      order: 1;
    }

    ${StyledTextContainer} {
      order: 2;
    }
  }
`;

export const StyledDescription = styled.ul`
  font-size: ${({ theme }) => theme.font.size.lg};
  margin-bottom: 40px;
  text-align: start;
  padding: 0;

  strong {
    color: ${({ theme }) => theme.palette.primary};
  }

  li {
    list-style: none;
    display: flex;
    align-items: flex-start;
    padding: 10px 20px;
    border-left: 4px solid #eaecf0;

    &:first-child {
      border-color: ${({ theme }) => theme.palette.primary};
    }
  }

  & .item-icon {
    margin: 2px 10px 0 0;
    color: ${({ theme }) => theme.palette.primary};

    @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
      font-size: 16px;
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
    display: flex;
    flex-direction: column;
    align-self: center;
  }
`;
