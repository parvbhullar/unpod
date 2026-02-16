import styled from 'styled-components';

export const StyledTabContent = styled.div`
  opacity: 0;
  height: 0;
  width: 0;
  overflow: hidden;
  transition: all 0.3s ease;

  .ant-tabs-content {
    padding: 0 !important;
  }

  &.active {
    opacity: 1;
    height: auto;
    width: auto;
  }
`;

export const StyledDetailsRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  //height: calc(100vh - 120px);
  height: calc(100vh - 60px);
  overflow-y: auto;
  text-overflow: ellipsis;
  overflow-x: hidden;
`;

export const StyledTabWrapper = styled.div`
  padding: 12px 32px;
`;
