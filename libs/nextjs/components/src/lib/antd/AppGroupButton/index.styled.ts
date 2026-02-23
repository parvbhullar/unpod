import styled from 'styled-components';

export const StyledButtonWrapper = styled.div`
  display: flex;

  & .ant-btn {
    margin: 0 !important;
    min-width: 50px;

    &:not(:first-child) {
      border-left-color: ${({theme}) => theme.palette.background.default};
    }

    &:not(.ant-btn-background-ghost) {
      border: 1px solid ${({theme}) => theme.palette.primary};
    }
  }
`;
