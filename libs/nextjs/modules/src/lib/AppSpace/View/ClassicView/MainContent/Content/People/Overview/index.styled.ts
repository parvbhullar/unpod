import styled from 'styled-components';
import {Typography} from 'antd';

const {Text} = Typography;

export const StyledRoot = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  height: calc(100vh - 180px);
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledDateHeader = styled(Text)`
  font-size: 14px;
  text-transform: uppercase;
  margin-bottom: ${({theme}) => theme.space.xss} !important;
`;

export const StyledDocumentsList = styled.div`
  padding: 16px 32px;
  width: 100%;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  background-color: ${({theme}) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 8px 10px;
  }
`;
