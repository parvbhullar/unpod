import styled from 'styled-components';
import {Button, Input} from 'antd';

const {TextArea} = Input;

export const StyledContainer = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  position: relative;
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
  padding: 16px 16px 12px 16px;
`;

export const StyledInput = styled(TextArea)`
  padding: 4px 0;
  resize: none;
`;

export const StyledMainContent = styled.div`
  margin-bottom: 12px;
  transition: all 0.4s linear;
  min-height: 86px;
  height: auto;

  &.active {
    min-height: 160px;
    height: auto;
  }
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
`;

export const StyledIconButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 !important;
  height: 36px !important;

  &:hover {
    background: transparent !important;
  }
`;

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px !important;
  height: 36px !important;
`;
