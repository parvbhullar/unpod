import styled from 'styled-components';
import {Button} from 'antd';
import {GlobalTheme} from '@unpod/constants';

export const StyledHeaderRow = styled.div`
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 10px;
  position: sticky;
  top: 0;
  //margin-bottom: 1em;
  border-bottom: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.border.color};
  background: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  padding: 1px 6px 6px;
  z-index: 101;
`;

export const StyledActionRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  position: sticky;
  bottom: 0;
  border-top: 1px solid
    ${({theme}: { theme: GlobalTheme }) => theme.border.color};
  background: ${({theme}: { theme: GlobalTheme }) =>
  theme.palette.background.default};
  padding: 16px 0;
  z-index: 101;
`;

export const StyledList = styled.div`
  display: flex;
  flex-direction: column;
  row-gap: 12px;
  //margin-bottom: 20px;
  padding-top: 12px;

  @media screen and (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    row-gap: 24px;
  }
`;

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
`;

export const StyledSchemaBody = styled.div`
  position: relative;
`;

export const StyledCopyWrapper = styled.div`
  position: absolute;
  top: -40px;
  right: 22px;
  bottom: auto;
  left: auto;
  z-index: 1;
`;
