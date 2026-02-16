import styled from 'styled-components';
import { Button, Typography } from 'antd';

const { Text } = Typography;

export const StyledContainer = styled.div`
  margin: auto;
  padding: 20px;
  width: 430px;
  max-width: 100%;
  text-align: center;
`;

export const StyledButton = styled(Button)`
  padding: 4px 15px !important;
  height: 36px !important;
`;

export const StyledConnector = styled.div`
  border: 1px solid ${({ theme }) => theme.palette.primary};
  border-radius: 40px;
  padding: 6px 14px;
  line-height: 1.5;
`;

export const StyledConnectorTitle = styled(Text)`
  text-transform: capitalize;
  font-weight: 600;
`;
