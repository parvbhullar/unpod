import styled from 'styled-components';
import {Input, Tag, Typography} from 'antd';
import {rgba} from 'polished';

const {Title} = Typography;

export const StyledIconWrapper = styled.span`
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

export const StyledTitleBlock = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

export const StyledAnchorTag = styled.a`
  display: inline-flex;
  align-items: center;
  color: ${({theme}) => theme.palette.text.primary};
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

export const StyledMainTitle = styled(Title)`
  font-size: 16px !important;
  margin-bottom: 0 !important;

  &.smart-heading {
    font-size: 24px !important;
    font-weight: ${({theme}) => theme.font.weight.medium} !important;
    margin: 0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;

    & > * {
      flex-shrink: 0;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
      font-size: 20px !important;
      width: 70%;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
      font-size: 20px !important;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.lg - 150}px) {
      font-size: 20px !important;
      width: 50%;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
      font-size: 18px !important;
      width: 80%;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
      font-size: 16px !important;
      width: 80%;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.xss}px) {
      font-size: 16px !important;
      width: 60%;
    }
  }
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

export const StyledLabel = styled(Tag)`
  margin-inline-end: 0;
  text-transform: capitalize;
  font-size: 10px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    display: none;
  }
`;

export const StyledLoader = styled.div`
  position: relative;
  display: flex;
  padding: 7px 11px;
  min-height: 100px;
`;
