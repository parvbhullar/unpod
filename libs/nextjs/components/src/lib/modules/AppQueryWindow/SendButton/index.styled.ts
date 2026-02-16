import styled from 'styled-components';
import { Button, Dropdown } from 'antd';

export const StyledButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px !important;
  height: 36px !important;
`;

export const StyledDropdownButton = styled(Dropdown.Button)`
  & .ant-btn {
    height: 36px !important;
    padding: 4px 12px !important;

    &.ant-dropdown-trigger {
      padding-inline-start: 6px;
    }

    &.ant-btn-compact-first-item {
      border-start-end-radius: 0 !important;
      border-end-end-radius: 0 !important;
    }

    &.ant-btn-compact-last-item {
      border-start-start-radius: 0 !important;
      border-end-start-radius: 0 !important;
    }
  }
`;

export const StyledModalContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 0;
  max-height: 75vh;
  overflow: hidden;
`;

export const StyledCalendarRoot = styled.div`
  display: flex;
  flex-wrap: nowrap;
  gap: 24px;
  margin: 6px 16px;
  overflow-y: auto;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-wrap: wrap;
  }
`;

export const StyledCalendarWrapper = styled.div`
  flex: 1;
`;

export const StyledInputsWrapper = styled.div`
  width: 40%;
  min-width: 300px;
  margin-block-start: 5px;
`;

export const StyledMenu = styled.menu`
  padding: 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 260px;
  min-width: 220px;
  overflow-y: auto;
`;

export const StyledMenuItem = styled.li`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: ${({ theme }) => theme.palette.text.primary};
  padding: 7px 16px;
  width: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &.disabled {
    color: ${({ theme }) => theme.palette.text.secondary};
    pointer-events: none;
  }

  & .menu-label {
    flex: 1;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  &:hover {
    background-color: ${({ theme }) => theme.palette.primaryHover};
  }

  &.active {
    background-color: ${({ theme }) => theme.palette.primaryHover};
    color: ${({ theme }) => theme.palette.primary};
  }
`;
