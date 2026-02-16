import styled from 'styled-components';
import { Button, Layout, Typography } from 'antd';

const { Header } = Layout;
const { Title } = Typography;

export const StyledHeader = styled(Header)`
  display: flex;
  align-items: center;
  padding: 10px 16px !important;
  /*background: linear-gradient(
    90deg,
    rgba(138, 119, 255, 0.14) 50%,
    rgba(245, 136, 255, 0.14) 100%
  );*/
  position: sticky;
  top: 0;
  width: 100%;
  z-index: 101;
  /*border-bottom: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 10px 10px 0 0;*/

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    padding: 10px 10px !important;
  }
`;

export const StyledContainer = styled.div<{ $hasCenter?: boolean }>`
  display: grid;
  grid-template-columns: ${({ $hasCenter }) =>
    $hasCenter ? '1fr auto 1fr' : '1fr auto'};
  gap: 16px;
  /*display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;*/
  flex: 1;
`;

export const StyledLeftContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const StyledRightContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  min-width: 0;
`;

export const StyledCenterContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
`;

export const StyledTitleWrapper = styled.div<{ $isScrolled?: boolean }>`
  padding: 4px 16px !important;
  background: ${({ $isScrolled }) =>
    $isScrolled ? 'rgba(138, 119, 255, 0.99)' : 'rgba(138, 119, 255, 0.66)'};
  border-radius: 20px;
  transition: background-color 0.3s;
`;

export const StyledTitleBlock = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
`;

export const StyledMainTitle = styled(Title)`
  font-size: 18px !important;
  line-height: 1.4 !important;
`;

export const StyledListingBtn = styled.div`
  cursor: pointer;

  @media (max-width: ${({ theme }) => theme.breakpoints.xs + 100}px) {
    display: none;
  }
`;

export const StyledButton = styled(Button)`
  display: flex;
  align-items: center;
  padding: 4px 10px !important;
  height: 32px !important;
  gap: 6px;
`;
