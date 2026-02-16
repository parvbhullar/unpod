import styled from 'styled-components';
import { Typography } from 'antd';

const { Text } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.space.lg};
  padding-top: 24px;
`;

export const StyledContent = styled.div`
  margin-bottom: ${({ theme }) => theme.space.xl};
`;

export const StyledContainer = styled.div`
  position: sticky;
  bottom: 0;
  border-top: 1px solid ${({ theme }) => theme.border.color};
  background: ${({ theme }) => theme.palette.background.default};
  padding: 24px 0;
`;

export const StyledText = styled(Text)`
  text-transform: capitalize;
`;
