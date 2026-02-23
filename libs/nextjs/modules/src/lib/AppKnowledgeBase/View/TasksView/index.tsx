'use client';
import {useEffect, useState} from 'react';
import {useGetDataApi} from '@unpod/providers';
import AppTable from '@unpod/components/third-party/AppTable';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import AppLoadingMore from '@unpod/components/common/AppLoadingMore';
import AppLoader from '@unpod/components/common/AppLoader';
import {getColumns} from './columns';
import {StyledRoot} from './index.styled';
import AppColumnZoomView from '@unpod/components/common/AppColumnZoomView';
import {AppDrawer} from '@unpod/components/antd';
import {useIntl} from 'react-intl';

const PAGE_SIZE = 50;

type TasksViewProps = {
  currentKb: any;
};

const AppTableAny = AppTable as any;

const TasksView = ({currentKb}: TasksViewProps) => {
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState<any[]>([]);
  const [selectedCol, setSelectedCol] = useState<any>(null);
  const {formatMessage} = useIntl();

  const [
    {apiData, loading, isLoadingMore},
    {setQueryParams, setLoadingMore},
  ] = useGetDataApi(`tasks/space-task/${currentKb?.token}/`, {data: []}, {
    page: 1,
    page_size: PAGE_SIZE,
  }) as any;

  useEffect(() => {
    if (currentKb?.token && currentKb?.final_role !== ACCESS_ROLE.GUEST) {
      setQueryParams({page: page, page_size: PAGE_SIZE});
    }
  }, [page, currentKb?.token]);

  useEffect(() => {
    if (apiData?.data) {
      if (page === 1) {
        setRecords(apiData.data);
      } else {
        setRecords((prevData) => [...prevData, ...apiData.data]);
      }
    }
  }, [apiData]);

  const onScrolledToBottom = () => {
    if (records.length > 0 && records.length === page * PAGE_SIZE) {
      const nextPage = page + 1;
      setLoadingMore(true);
      setPage(nextPage);
    }
  };

  return (
    <StyledRoot>
      {/*<pre>{JSON.stringify(apiData, null, 4)}</pre>*/}
      {loading && !isLoadingMore && <AppLoader position="absolute"/>}

      <AppTableAny
        rowKey="id"
        columns={getColumns(setSelectedCol, formatMessage)}
        dataSource={records}
        size="middle"
        pagination={false}
        onScrolledToBottom={onScrolledToBottom}
        allowGridActions
        configuration={{
          showSerialNoRow: false,
          allowEditorToolbar: false,
          allowCountFooter: false,
          allowFormula: false,
        }}
        extraHeight={33}
      />

      {isLoadingMore && <AppLoadingMore/>}

      <AppDrawer
        title={selectedCol?.title}
        open={selectedCol !== null}
        destroyOnHidden={true}
        onClose={() => setSelectedCol(null)}
        styles={{body: {padding: 0, position: 'relative'}}}
        width="60%"
      >
        <AppColumnZoomView selectedCol={selectedCol}/>
      </AppDrawer>
    </StyledRoot>
  );
};

export default TasksView;
