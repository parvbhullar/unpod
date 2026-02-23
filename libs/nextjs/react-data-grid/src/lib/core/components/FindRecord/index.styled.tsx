import styled from 'styled-components';
import {Input} from 'antd';

export const StyledContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
  padding: 14px 12px 12px 12px;
  border: 1px solid ${({theme}: { theme: any }) => theme.table.borderColor};
  border-radius: 0 0 20px 20px;
  position: absolute;
  top: -15px;
  right: 0;
  left: auto;
  bottom: auto;
  z-index: 10;
  background: #fff;
  transform: translateY(-100%);
  opacity: 0;
  transition: transform 0.5s,
  opacity 0.3s;

  &.open {
    transform: translateY(0);
    opacity: 1;
  }

  @media screen and (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    flex-wrap: wrap;
  }
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
`;

export const StyledInput = styled(Input)`
  border-radius: ${({theme}) => theme.radius.sm}px;
  height: 36px;
  margin-bottom: 0;
`;
