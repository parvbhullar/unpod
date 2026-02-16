import styled from 'styled-components';
import { Typography } from 'antd';
import { GlobalTheme } from '@unpod/constants';

const { Text } = Typography;

export const StyledRoot = styled.div`
  padding: 24px;
  min-height: 100%;

  & .app-setting-root:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
`;

export const StyledConnector = styled.div`
  border: 1px solid
    ${({ theme }: { theme: GlobalTheme }) => theme.palette.primary};
  border-radius: 40px;
  padding: 6px 14px;
  line-height: 1.5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
`;

export const StyledConnectorTitle = styled(Text)`
  text-transform: capitalize;
  font-weight: 600;
`;
