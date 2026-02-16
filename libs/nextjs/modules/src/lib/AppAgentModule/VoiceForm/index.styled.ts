import styled from 'styled-components';

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;

export const CollapseWrapper = styled.div`
  .ant-collapse {
    background: ${({ theme }) => theme.palette.background.default} !important;
    border: none;
    overflow: hidden;
    border-radius: 8px;
  }

  .ant-collapse-content-box {
    padding: 20px !important;
  }

  .ant-collapse > .ant-collapse-item {
    margin-bottom: 16px;
    overflow: hidden;
    border: 1px solid ${({ theme }) => theme.border.color};
    border-radius: 8px;
  }

  .ant-collapse-header {
    align-items: center !important;
  }

  .ant-checkbox-inner {
    border-radius: 4px !important;
  }
`;

export const StyledCollapseItemRow = styled.div`
  .ant-form-item {
    margin-bottom: 0 !important;
  }
`;

export const StyledCollapseItem = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
`;

export const StyledModelOption = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
`;
