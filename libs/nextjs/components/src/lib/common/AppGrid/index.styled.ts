import styled from 'styled-components';

export const StyledListFooter = styled.div`
  padding: 10px;
  color: ${({ theme }) => theme.palette.text.secondary};
  display: flex;
  justify-content: center;
`;

export const StyledLoaderProgress = styled.div`
  width: 100%;
  display: flex;
  justify-content: center;
  color: ${({ theme }) => theme.palette.text.secondary};
  padding: 8px;

  & span {
    margin-left: 8px;

    [dir='rtl'] & {
      margin-left: 0;
      margin-right: 8px;
    }
  }
`;

export const StyledGridContainer = styled.div`
  width: 100%;
`;

export const StyledGridColumnCount = styled.div`
  flex-grow: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
`;
