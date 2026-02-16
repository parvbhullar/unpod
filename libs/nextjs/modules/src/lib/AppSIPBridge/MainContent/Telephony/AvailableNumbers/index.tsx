import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from 'antd';
import { useAuthContext, usePaginatedDataApi } from '@unpod/providers';
import NumberCard from '../NumberCard';
import AppList from '@unpod/components/common/AppList';
import { DrawerBody } from '@unpod/components/antd/AppDrawer/DrawerBody';
import { DrawerFooter } from '@unpod/components/antd/AppDrawer/DrawerFooter';
import { getRemainingChannels } from '@unpod/helpers/PaymentHelper';
import { useIntl } from 'react-intl';
import SearchBox from '@unpod/components/common/AppSidebar/SearchBox';
import { SearchBoxWrapper } from './index.styled';

type AvailableNumbersProps = {
  open: boolean;
  onClose: () => void;
  selectedNumbers: any[];
  onSelectionDone: (numbers: any[], reCallApi: () => void) => void;
};

const AvailableNumbers = ({
  open,
  onClose,
  selectedNumbers,
  onSelectionDone,
}: AvailableNumbersProps) => {
  const [selectedNo, setSelectedNo] = useState<any[]>(selectedNumbers || []);
  const { subscription } = useAuthContext();
  const router = useRouter();
  const channelCountRef = useRef(
    getRemainingChannels((subscription as any)?.modules),
  );
  const [searchValue, setSearchValue] = useState('');
  const { formatMessage } = useIntl();

  const isChannelAvailable = () => {
    return (
      channelCountRef.current - (selectedNo.length - selectedNumbers.length) > 0
    );
  };

  const [
    { apiData, loading, isLoadingMore, hasMoreRecord },
    { setPage, setAllowApiCall },
  ] = usePaginatedDataApi<any[]>(`core/telephony-numbers/`, [], {}, open);

  useEffect(() => {
    if (open) setAllowApiCall(true);
  }, [open]);

  useEffect(() => {
    setSelectedNo(selectedNumbers || []);
  }, [selectedNumbers]);

  const onToggleSelect = (item: any) => () => {
    const isAlreadySelected = selectedNo.some(
      (number) => number.number === item.number,
    );

    if (!isChannelAvailable() && !isAlreadySelected) {
      router.push('/upgrade');
      return;
    }

    if (isAlreadySelected) {
      setSelectedNo((prev: any[]) =>
        prev.filter((number: any) => number.number !== item.number),
      );
    } else {
      setSelectedNo((prev: any[]) => [...prev, item]);
    }
  };

  const reCallAPI = () => {
    setSelectedNo([]);
    setPage(1);
  };

  const onSelectionConfirm = () => {
    onSelectionDone(selectedNo, reCallAPI);
  };

  const onSearch = (value: string) => {
    setSearchValue(value || '');
  };

  const filteredData = useMemo(() => {
    if (!searchValue || searchValue.length < 3) {
      return apiData;
    }

    return apiData?.filter((item: any) =>
      item.number?.toString().includes(searchValue),
    );
  }, [apiData, searchValue]);

  const NumberCardAny = NumberCard as any;

  return (
    <>
      <DrawerBody bodyHeight={170}>
        <SearchBoxWrapper>
          <SearchBox onSearch={onSearch} />
        </SearchBoxWrapper>
        <AppList
          data={filteredData}
          loading={loading}
          renderItem={(item: any, index: number) => (
            <NumberCardAny
              key={index}
              item={item}
              onClick={onToggleSelect(item)}
              selected={selectedNo.some(
                (selectedItem: any) => selectedItem.id === item.id,
              )}
              btnLabel={
                isChannelAvailable()
                  ? formatMessage({ id: 'common.select' })
                  : formatMessage({ id: 'common.upgrade' })
              }
              selectedBtnLabel={formatMessage({ id: 'common.unselect' })}
            />
          )}
          noDataMessage={formatMessage({ id: 'bridge.numberNoDataMessage' })}
          footerProps={{
            loading: isLoadingMore,
            hasMoreRecord,
          }}
        />
      </DrawerBody>
      <DrawerFooter>
        <Button
          ghost
          type="primary"
          onClick={() => {
            setSelectedNo(selectedNumbers || []);
            onClose();
          }}
        >
          {formatMessage({ id: 'common.cancel' })}
        </Button>
        {apiData?.length > 0 && (
          <Button type="primary" onClick={onSelectionConfirm}>
            {formatMessage({ id: 'common.save' })}
          </Button>
        )}
      </DrawerFooter>
    </>
  );
};

export default AvailableNumbers;
