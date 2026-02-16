import { useCallback, useEffect, useState } from 'react';
import {
  deleteDataApi,
  getDataApi,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppTable from '@unpod/components/third-party/AppTable';
import { getColumns } from './columns';
import EditTrunk from './EditTrunk';
import { useIntl } from 'react-intl';

const PAGE_SIZE = 50;

const AppTableAny = AppTable as any;

const Trunks = ({ sipBridge }: { sipBridge: any }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [openEdit, setOpenEdit] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const { formatMessage } = useIntl();

  const [{ apiData, loading }, { setLoadingMore, setQueryParams }] =
    useGetDataApi(
      `telephony/trunks/`,
      { data: [] },
      { page: 1, page_size: PAGE_SIZE },
      false,
    ) as any;

  const resetData = useCallback(() => {
    setRecords([]);
    setPage(1);
  }, []);

  useEffect(() => {
    if (sipBridge) {
      resetData();
      setQueryParams({ page: 1, bridge: sipBridge.slug });
    }
  }, [sipBridge, resetData]);

  useEffect(() => {
    if (page) setQueryParams({ page: page });
  }, [page]);

  useEffect(() => {
    if (apiData?.data) {
      setRecords((prevData: any[]) => {
        if (prevData.length === 0) {
          return apiData.data;
        }
        return [...prevData, ...apiData.data];
      });
    }
  }, [apiData]);

  const onScrolledToBottom = () => {
    if (records.length > 0 && records.length === page * PAGE_SIZE) {
      const nextPage = page + 1;
      setLoadingMore(true);
      setPage(nextPage);
    }
  };

  const onEditClick = (item: any) => {
    setLoadingDetail(true);
    getDataApi(`telephony/trunks/${item.id}/`, infoViewActionsContext)
      .then((res: any) => {
        setLoadingDetail(false);

        if (res?.data) {
          setSelectedItem(res.data);
          setOpenEdit(true);
        } else {
          infoViewActionsContext.showError(
            formatMessage({ id: 'bridge.trunksFetchError' }),
          );
        }
      })
      .catch((err: any) => {
        setLoadingDetail(false);
        infoViewActionsContext.showError(err?.message);
      });
  };

  const onUpdated = (newItem: any) => {
    setRecords((prev: any[]) =>
      prev.map((rec: any) => (rec.id === newItem.id ? newItem : rec)),
    );
    setOpenEdit(false);
    setSelectedItem(null);
  };

  const onDeleteConfirm = (item: any) => {
    deleteDataApi(`telephony/trunks/${item.id}/`, infoViewActionsContext)
      .then((res: any) => {
        setRecords((prev: any[]) =>
          prev.filter((rec: any) => rec.id !== item.id),
        );
        infoViewActionsContext.showMessage(res?.message);
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err?.message);
      });
  };

  return (
    <>
      <AppTableAny
        rowKey="id"
        columns={getColumns({ onEditClick, onDeleteConfirm, formatMessage })}
        dataSource={records}
        size="middle"
        pagination={false}
        loading={loading || loadingDetail}
        onScrolledToBottom={onScrolledToBottom}
        extraHeight={20}
        fullHeight
      />

      {selectedItem && (
        <EditTrunk
          item={selectedItem}
          open={openEdit}
          onClose={() => setOpenEdit(false)}
          onUpdated={onUpdated}
        />
      )}
    </>
  );
};

export default Trunks;
