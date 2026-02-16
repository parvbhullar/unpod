'use client';
import {
  type ComponentType,
  isValidElement,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Divider, Form } from 'antd';
import { useRouter } from 'next/navigation';
import {
  patchDataApi,
  postDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppLoader from '@unpod/components/common/AppLoader';
import BridgeHeader from './BridgeHeader';
import { StyledRoot, StyledTabsWrapper } from './index.styled';
import { getTabItems } from '../constants';
import { AppTabs } from '@unpod/components/antd';
import {
  useAppModuleActionsContext,
  useAppModuleContext,
} from '@unpod/providers/AppModuleContextProvider';
import { BridgeStudioSkeleton, IsNewStudioSkeleton } from '@unpod/skeleton';
import { useSkeleton } from '@unpod/custom-hooks/useSkeleton';
import { useIntl } from 'react-intl';

type MainContentProps = {
  bridge?: any;
  isNew?: boolean;
};

const MainContent = ({ bridge, isNew }: MainContentProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedNumbers, setSelectedNumbers] = useState<any[]>([]);
  const [form] = Form.useForm();
  const bridgeHeaderRef = useRef<any>({ form });
  const { isNewRecord, record, listData } = useAppModuleContext() as any;
  const { formatMessage } = useIntl();
  const {
    setRecord,
    setIsNewRecord,
    deleteRecord,
    updateRecord,
    addNewRecord,
  } = useAppModuleActionsContext() as any;
  const { isPageLoading, skeleton: SkeletonComponent } = useSkeleton(
    BridgeStudioSkeleton as ComponentType<unknown>,
    IsNewStudioSkeleton as ComponentType<unknown>,
  );
  const SkeletonView = isValidElement(SkeletonComponent) ? (
    SkeletonComponent
  ) : (
    <SkeletonComponent />
  );

  useEffect(() => {
    if (bridge) {
      setRecord(bridge);
    }
  }, [bridge]);

  useEffect(() => {
    if (isNew) {
      setRecord(null as any);
      setIsNewRecord(isNew);
    }
  }, [isNew]);

  useEffect(() => {
    if (record?.numbers) setSelectedNumbers(record?.numbers || []);
  }, [record]);

  const saveBridgeData = (payload: any, callBackFun?: () => void) => {
    setLoading(true);

    if (record) {
      patchDataApi(
        `telephony/bridges/${record.slug}/`,
        infoViewActionsContext,
        payload,
      )
        .then((response: any) => {
          setLoading(false);
          infoViewActionsContext.showMessage(response?.message);
          setRecord(response.data);
          updateRecord(response.data);
          callBackFun?.();
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    } else {
      postDataApi('telephony/bridges/', infoViewActionsContext, payload)
        .then((response: any) => {
          setLoading(false);
          infoViewActionsContext.showMessage(response?.message);
          setRecord(response.data);
          setIsNewRecord(false);
          addNewRecord(response.data);
          router.push(`/bridges/${response.data.slug}?tab=telephony`);
          //setActiveTab('telephony');
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    }
  };

  const onBridgeDelete = () => {
    deleteRecord(record.slug);
    if (listData.apiData.length > 1) {
      if (listData.apiData[0].slug === record.slug) {
        router.push(`/bridges/${listData.apiData[1].slug}`);
      } else {
        router.push(`/bridges/${listData.apiData[0].slug}`);
      }
    } else {
      router.push(`/bridges/new/`);
    }
  };

  if ((!record && !isNew) || isPageLoading) {
    return SkeletonView;
  }

  return (
    <StyledRoot>
      <BridgeHeader
        sipBridge={record}
        selectedNumbers={selectedNumbers}
        saveBridgeData={saveBridgeData}
        loading={loading}
        onBridgeDelete={onBridgeDelete}
        ref={bridgeHeaderRef}
      />
      <Divider style={{ margin: '0 0 5px 0' }} />

      <StyledTabsWrapper>
        <AppTabs
          items={getTabItems({
            isNewRecord,
            sipBridge: record,
            selectedNumbers,
            setSelectedNumbers,
            saveBridgeData,
            headerRef: bridgeHeaderRef,
            formatMessage,
          })}
          routePath={`/bridges/${record?.slug}`}
        />
      </StyledTabsWrapper>
      {loading && <AppLoader />}
    </StyledRoot>
  );
};
export default MainContent;
