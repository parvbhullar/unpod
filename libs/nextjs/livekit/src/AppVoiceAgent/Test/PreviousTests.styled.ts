import styled from 'styled-components';
import { GlobalTheme } from '@unpod/constants';
import { Flex } from 'antd';

type StyledFlexProps = {
  $mb?: number;
};

export const TestsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
`;

export const TestsContent = styled.div<{ $startCall?: boolean | undefined }>`
  display: flex;
  max-height: ${({ $startCall }) =>
    $startCall ? '370px' : 'calc(100vh - 196px)'};
  overflow-y: auto;
`;

export const TestResultContent = styled.div<{
  $startCall?: boolean | undefined;
}>`
  display: flex;
  max-height: calc(100vh - 60px);
  overflow-y: auto;
`;

export const TestCard = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  margin: 6px 16px;
  background-color: ${({ theme }: { theme: GlobalTheme }) =>
    theme.palette.background.component};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

export const TestInfo = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 2px;
`;

export const TestMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.text.secondary};
`;

export const StyledFlex = styled(Flex)<StyledFlexProps>`
  margin-bottom: ${({ $mb = 0 }) => `${$mb}px`};
  width: 100%;
`;
