import styled from 'styled-components';
import {Typography} from 'antd';
import {rgba} from 'polished';

const {Paragraph} = Typography;

export const StyledInfoWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 16px 10px;

  & .ant-typography {
    margin: 0;
  }
`;

export const StyledSumResult = styled(Paragraph)`
  padding: 7px 16px;
  background-color: ${({theme}) => rgba(theme.primaryColor, 0.2)};
`;

export const StyledMenu = styled.menu`
  padding: 10px 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 80vh;
  overflow-y: auto;
`;

export const StyledMenuItem = styled.li`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({theme}) => theme.text.heading};
  padding: 7px 10px;
  // border-radius: 8px;
  width: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({theme}) => rgba(theme.primaryColor, 0.2)};
  }
`;
