import styled from 'styled-components';
import {Input, Tag, Typography} from 'antd';
import {rgba} from 'polished';

const {Title} = Typography;

export const StyledDropdownArrow = styled.span`
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;

  & > svg:first-child {
    margin-bottom: -6px;
  }

  & > svg:last-child {
    margin-top: -6px;
  }
`;

export const StyledSubMenuItem = styled.span`
  display: flex;
  align-items: center;

  &.add-new-title {
    color: ${({theme}) => theme.palette.primary};
  }

  & > svg {
    min-width: 16px;
  }
`;

export const StyledSubMenuText = styled.span`
  margin-left: 10px;
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const StyledIconWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    display: none;
  }
`;

export const StyledTitleBlock = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
`;

export const StyledTitleContent = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
`;

export const StyledLabel = styled(Tag)`
  margin-inline-end: 0;
  text-transform: capitalize;
  font-size: 10px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    display: none;
  }
`;

export const StyledMainTitle = styled(Title)`
  font-size: 18px !important;
  margin-bottom: 0 !important;
`;

export const StyledMenusContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 0;
  max-height: 75vh;
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

export const StyledAddButton = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({theme}) => theme.palette.text.heading};
  padding: 7px 11px;
  width: 100%;
  cursor: pointer;
  background-color: ${({theme}) => rgba(theme.palette.success, 0.2)};
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({theme}) => rgba(theme.palette.success, 0.4)};
  }
`;

export const StyledLoader = styled.div`
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  z-index: 100;
`;
