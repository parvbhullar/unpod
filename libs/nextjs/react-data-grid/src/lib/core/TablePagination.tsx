import {Pagination, type TablePaginationConfig} from 'antd';
import styled from 'styled-components';

const StyledPagination = styled(Pagination)`
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  background: ${({theme}: { theme: any }) => theme.backgroundColor};
  position: sticky;
  bottom: 0;
  padding: 20px 0 12px;
  z-index: 101;

  & .ant-pagination-total-text {
    margin-right: auto;
    line-height: 32px;
  }

  & .ant-pagination-options {
    margin-left: auto;

    & .ant-select-selection-item {
      line-height: 25px !important;
    }
  }
`;

export const getTablePagination = (
  pageSize = 10,
  currentPage = 1,
  dataCount = 0,
  onShowSizeChange?: (current: number, size: number) => void,
  onPageChange?: (page: number, pageSize: number) => void,
  customPageSizeOptions?: string[],
) => {
  return {
    pageSize,
    current: currentPage,
    total: dataCount,
    onShowSizeChange,
    onChange: onPageChange,
    showSizeChanger: true,
    position: ['bottomCenter'],
    showTotal: (total: number) => `Total ${total} items`,
    pageSizeOptions: customPageSizeOptions ?? [
      '5',
      '10',
      '20',
      '50',
      '100',
      '500',
      '1000',
    ],
  } as TablePaginationConfig;
};

function TablePagination(props: TablePaginationConfig) {
  return <StyledPagination {...props} />;
}

export default TablePagination;
