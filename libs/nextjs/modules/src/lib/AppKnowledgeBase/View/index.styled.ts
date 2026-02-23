import styled from 'styled-components';
import {Button, Typography} from 'antd';

const {Title} = Typography;

export const StyledTableRoot = styled.div`
  padding: 0;
`;

export const IconWrapper = styled.span`
  cursor: pointer;
`;

export const StyledContainer = styled.div`
  margin: 15px auto;
`;

export const StyledButton = styled(Button)`
  display: flex;
  align-items: center;
  padding: 4px 10px !important;
  height: 32px !important;
  gap: 6px;
`;

export const StyledUploadRoot = styled.div`
  padding: 16px;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius};
  min-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
`;

export const StyledNoAccessContainer = styled.div`
  margin: 16px auto;
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
`;

export const StyledNoAccessText = styled(Title)`
  text-align: center;
`;
