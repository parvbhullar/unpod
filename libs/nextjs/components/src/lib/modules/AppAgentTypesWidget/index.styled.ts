import styled from 'styled-components';
import {GlobalTheme} from '@unpod/constants';

export const StyledRoot = styled('div')`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 32px 0 24px 0;
  width: 100%;

  @media (max-width: 768px) {
    gap: 16px;
  }
`;

export const StyledContainer = styled('div')`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  align-items: center;
  gap: 12px;
  width: 100%;
`;

export const StyledItemRoot = styled('div')`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  border: 1px solid ${({theme}: { theme: GlobalTheme }) => theme.border.color};
  border-radius: 16px;
  cursor: pointer;
  max-width: 100%;
  height: 100%;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.component};
  }
`;

export const StyledContent = styled('div')`
  margin: 0;
`;

export const StyledTitleWrapper = styled('div')`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 1em;

  & .ant-typography {
    margin: 0 !important;
  }
`;
