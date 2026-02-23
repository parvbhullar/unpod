import styled from 'styled-components';
import AppList from '../../common/AppList';
import {Row} from 'antd';
import SimpleBar from 'simplebar-react';
import {GlobalTheme} from '@unpod/constants';

export const StyledRow = styled(Row)`
  padding: 16px;
`;

export const StyledRootContainer = styled.div`
  flex: 1;
  width: ${({theme}: { theme: GlobalTheme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
`;

export const StyledScrollbar = styled(SimpleBar)`
  height: calc(100vh - 64px);

  & .simplebar-content {
    min-height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
  }
`;

export const StyledList = styled(AppList as any)`
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;

  & div:last-child .space-post-item {
    border-bottom: none;
  }

  .ant-list-item {
    cursor: pointer;
    padding: 16px;

    &:hover {
      box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
  }

  .ant-list-item-meta {
    flex-direction: column;
  }

  .ant-list-pagination {
    margin: 12px 0;
    text-align: start;
    padding: 0 16px;
  }
`;
