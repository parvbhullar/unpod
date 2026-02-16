import { useRef } from 'react';
import type { Pilot, Spaces } from '@unpod/constants/types';
import {
  getDataApi,
  uploadPutDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { Button } from 'antd';
import { StyledContainer, StyledSearchBoxWrapper } from './index.styled';
import { MdAdd } from 'react-icons/md';
import { useRouter } from 'next/navigation';
import { generateHandle } from '@unpod/helpers/StringHelper';
import SearchBox from '@unpod/components/common/AppSidebar/SearchBox';
import { DrawerBody } from '@unpod/components/antd/AppDrawer/DrawerBody';
import { DrawerFooter } from '@unpod/components/antd';
import AppList from '@unpod/components/common/AppList';
import LinkAgentItem from './LinkAgentItem';
import { useIntl } from 'react-intl';

type AgentData = {
  id?: string | number;
  handle?: string;
  name?: string;
  type?: string;
  space?: { slug?: string };
  [key: string]: unknown;
};

type ConfigureAgentModalProps = {
  currentSpace: Spaces | null;
  onClose: () => void;
  $bodyHeight: number;
};

const ConfigureAgentModal = ({
  currentSpace,
  onClose,
  $bodyHeight,
}: ConfigureAgentModalProps) => {
  const { activeOrg } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();
  const router = useRouter();
  const listRef = useRef(null);

  const [{ apiData, loading }, { setQueryParams, reCallAPI }] = useGetDataApi<
    Pilot[]
  >(
    'core/pilots/',
    { data: [] },
    {
      domain: activeOrg?.domain_handle,
      page_size: 20,
      page: 1,
    },
  );

  const updateAgentData = (formData: FormData, agentData: AgentData) => {
    const isLinked = agentData?.space?.slug === currentSpace?.slug;

    const url = isLinked
      ? `core/pilots/${agentData.handle}/unlink-space/`
      : `core/pilots/${agentData.handle}/`;

    const apiMethod = isLinked ? getDataApi : uploadPutDataApi;

    apiMethod(
      url,
      infoViewActionsContext,
      isLinked ? undefined : (formData as unknown as Record<string, unknown>),
    )
      .then((res) => {
        const response = res as { message?: string };
        infoViewActionsContext.showMessage(
          response?.message ||
            (isLinked
              ? formatMessage({ id: 'drawer.unlinked' })
              : formatMessage({ id: 'drawer.updated' })),
        );
        queueMicrotask(() => reCallAPI());
      })
      .catch((err) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const saveAgent = (agentData: AgentData) => {
    const formData = new FormData();

    const nameValue = typeof agentData?.name === 'string' ? agentData.name : '';
    const handleValue =
      typeof agentData?.handle === 'string'
        ? agentData.handle
        : generateHandle(nameValue);

    formData.append('handle', handleValue);

    formData.append('name', nameValue);
    formData.append('type', agentData?.type ? agentData?.type : 'Voice');
    if (currentSpace?.slug) formData.append('space_slug', currentSpace?.slug);

    updateAgentData(formData, agentData);
  };

  const onSearch = (value: string) => {
    setQueryParams({
      domain: activeOrg?.domain_handle,
      search: value,
      page: 1,
    });
  };

  return (
    <>
      <DrawerBody
        isTabDrawer={true}
        bodyHeight={$bodyHeight}
        style={{ overflow: 'auto', paddingTop: 0 }}
      >
        <StyledSearchBoxWrapper>
          <SearchBox onSearch={onSearch} variant="borderless" />
          <Button
            onClick={() => {
              router.push('/ai-studio/new/');
            }}
            type="primary"
            shape="round"
            ghost
            icon={<MdAdd size={18} />}
            size="small"
          >
            {formatMessage({ id: 'drawer.agent' })}
          </Button>
        </StyledSearchBoxWrapper>
        <StyledContainer ref={listRef}>
          <AppList
            key={currentSpace?.slug}
            data={apiData?.data ?? []}
            loading={loading}
            itemSpacing={16}
            renderItem={(item) => (
              <LinkAgentItem
                key={(item as AgentData).id}
                item={item as AgentData}
                currentSpace={currentSpace}
                saveAgent={saveAgent}
              />
            )}
          />
        </StyledContainer>
      </DrawerBody>
      <DrawerFooter>
        <Button
          onClick={() => {
            onClose();
          }}
          type="default"
          size="middle"
        >
          {formatMessage({ id: 'common.close' })}
        </Button>
      </DrawerFooter>
    </>
  );
};

export default ConfigureAgentModal;
