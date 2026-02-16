import styled from 'styled-components';
import { Typography } from 'antd';

const { Text } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.lg};
  height: calc(100vh - 105px);
`;

export const StyledContent = styled.div`
  margin-bottom: ${({ theme }) => theme.space.xl};
`;

export const StyledContainer = styled.div`
  margin-top: auto;
`;

export const StyledText = styled(Text)`
  text-transform: capitalize;
`;
