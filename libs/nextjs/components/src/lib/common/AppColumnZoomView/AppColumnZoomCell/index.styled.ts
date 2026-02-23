import styled from 'styled-components';
import {Typography} from 'antd';

const {Paragraph} = Typography;

export const StyledZoomContainer = styled(Paragraph)`
  position: absolute;
  right: 0;
  bottom: 0;
  padding: 2px 4px;
  background: ${({theme}) => theme.palette.background.component};
  border-radius: 10px;
  margin-bottom: 0 !important;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s ease;
`;

export const StyledCellContent = styled.div`
  position: relative;

  &:hover ${StyledZoomContainer} {
    opacity: 1;
  }

  & a.ant-typography {
    color: ${({theme}) => theme.palette.primary};
  }
`;
