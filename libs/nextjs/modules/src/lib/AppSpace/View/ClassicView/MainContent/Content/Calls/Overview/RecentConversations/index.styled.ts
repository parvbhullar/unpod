import styled from 'styled-components';
import {Card, Typography} from 'antd';

const {Text} = Typography;

export const StyledRoot = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
`;

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const StyledTimeText = styled(Text)`
  font-weight: ${({theme}) => theme.font.weight.regular} !important;
  text-align: center;
`;

export const StyledTimeRow = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
`;

export const StyledDot = styled.div`
  width: 4px;
  height: 4px;
  background: ${({theme}) => theme.palette.text.secondary};
  border-radius: 50%;
`;

export const StyledCard = styled(Card)`
  background-color: ${({theme}) => theme.palette.background.default};
  margin-bottom: 12px;

  .ant-card-head {
    padding: 6px 12px !important;
    min-height: 30px !important;
    border-bottom: none !important;
  }

  .ant-card-body {
    padding: 12px !important;
  }
`;

export const StyledFooter = styled.div`
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid ${({theme}) => theme.border.color};
  display: flex;
  align-items: center;
  gap: 16px;
`;

export const StyledText = styled(Text)`
  font-size: 12px;
`;

export const StyledTime = styled(Text)`
  font-size: 12px;
`;
