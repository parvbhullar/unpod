import styled from 'styled-components';
import { Input } from 'antd';
import { rgba } from 'polished';

export const StyledMenusContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 0;
  max-height: 75vh;
`;

export const StyledTitle = styled.div`
  font-weight: 600;
  padding: 0 10px;
`;

export const StyledInputWrapper = styled.div`
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 5px;
`;

export const StyledInput = styled(Input)`
  border-radius: 10px;
`;

export const StyledContent = styled.div`
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;

  p {
    padding: 0 10px;
  }
`;

export const StyledContentMain = styled.div`
  min-height: 100px;
  min-width: 150px;
  display: flex;
  p {
    padding: 0 10px;
  }
`;

export const StyledAddButton = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({ theme }) => theme.palette.text.heading};
  padding: 7px 11px;
  width: 100%;
  cursor: pointer;
  background-color: ${({ theme }) => rgba(theme.palette.success, 0.2)};
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({ theme }) => rgba(theme.palette.success, 0.4)};
  }
`;
