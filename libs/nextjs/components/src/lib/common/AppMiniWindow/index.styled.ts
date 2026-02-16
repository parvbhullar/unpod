import styled from 'styled-components';
import AppDrawer from '../../antd/AppDrawer';

export const StyledAppDrawer = styled(AppDrawer as any)`
  box-shadow:
    0 1px 20px rgba(16, 24, 40, 0.1),
    0 1px 10px rgba(16, 24, 40, 0.06);

  .ant-drawer-header {
    padding: 8px 16px;
    background: ${({ theme }) => theme.palette.background.colorPrimaryBg};
    border-bottom: 1px solid transparent;
  }

  .ant-drawer-title {
    font-weight: 500;
    font-size: 14px;
  }

  .ant-form-item-explain-error {
    margin-bottom: 0;
  }

  .ant-drawer-body {
    height: calc(100% - 41px);
    display: flex;
    flex-direction: column;
  }
`;

export const StyledWrapper = styled.div`
  height: 100%;

  .ant-form {
    height: 100%;
  }
`;

export const StyledBody = styled.div`
  height: calc(100% - 65px);
  padding: 8px 16px 16px 16px;
  display: flex;
  flex-direction: column;
`;

export const StyledFooter = styled.div`
  min-height: 58px;
  padding: 12px 16px;
  position: relative;
  border-top: 1px solid ${({ theme }) => theme.border.color};
`;
