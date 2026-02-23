import styled from 'styled-components';
import {Tag} from 'antd';

const {CheckableTag} = Tag;

export const StyledRoot = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
`;

export const StyledLabel = styled(CheckableTag)`
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0;
  padding: 4px 14px;
  border-radius: 12px;
  background: ${({theme}) => theme.palette.background.default};
  border: 1px solid ${({theme}) => theme.border.color};
  transition: all 0.2s ease;

  & > span {
    display: flex !important;
    align-items: center;
    gap: 8px;
  }

  &.ant-tag-checkable-checked {
    background: ${({theme}) => theme.palette.primaryHover};
    border: 1px solid ${({theme}) => theme.palette.primary};
  }
`;
