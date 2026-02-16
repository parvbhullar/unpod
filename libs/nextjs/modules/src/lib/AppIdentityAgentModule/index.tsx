'use client';
import { type ComponentType, isValidElement, useEffect, useMemo } from 'react';
import { Divider, Form } from 'antd';
import { useIntl } from 'react-intl';
import { usePathname, useRouter } from 'next/navigation';
import { StyledRoot, StyledTabsWrapper } from './index.styled';
import {
  uploadPostDataApi,
  uploadPutDataApi,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import AgentHeader from './AgentHeader';
import { generateHandle } from '@unpod/helpers/StringHelper';
import { getTabItems } from './constants';
import { AppTabs } from '@unpod/components/antd';
import {
  useAppModuleActionsContext,
  useAppModuleContext,
} from '@unpod/providers/AppModuleContextProvider';
import { useSkeleton } from '@unpod/custom-hooks';
import { AiIdentityStudioSkeleton } from '@unpod/skeleton/AIIdentityStudio';

type AppIdentityAgentModuleProps = {
  pilot?: any;
  isNew?: boolean;
  currentSpace?: any;
  path?: string;
};

const AppIdentityAgentModule = ({
  pilot,
  isNew,
  currentSpace,
}: AppIdentityAgentModuleProps) => {
  const { formatMessage } = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();
  useAppModuleActionsContext();
  const { record, isNewRecord } = useAppModuleContext() as any;
  const { setRecord, updateRecord, addNewRecord, setIsNewRecord } =
    useAppModuleActionsContext() as any;
  const { isPageLoading, skeleton: SkeletonComponent } = useSkeleton(
    AiIdentityStudioSkeleton as ComponentType<unknown>,
    AiIdentityStudioSkeleton as ComponentType<unknown>,
  );
  const SkeletonView = isValidElement(SkeletonComponent) ? (
    SkeletonComponent
  ) : (
    <SkeletonComponent />
  );

  const infoViewContext = useInfoViewContext();
  const router = useRouter();
  const [form] = Form.useForm();
  const pathname = usePathname();

  useEffect(() => {
    if (isNew) {
      setIsNewRecord(isNew);
    }
  }, [isNew]);

  useEffect(() => {
    if (pilot) {
      setRecord(pilot);
    }
  }, [pilot]);

  useEffect(() => {
    if (!pilot?.handle && currentSpace?.token) {
      const nextPilot = {
        ...pilot,
        name: currentSpace.name,
        handle: `space-agent-${currentSpace.token}`,
      };
      setRecord(nextPilot);
    }
  }, []);

  const updateAgentData = (formData: FormData) => {
    const nameValue = formData.get('name');
    const fallbackName = typeof nameValue === 'string' ? nameValue : '';
    formData.append(
      'handle',
      record?.handle ? record?.handle : generateHandle(fallbackName),
    );

    let apiMethod = uploadPutDataApi;
    if (isNewRecord) {
      apiMethod = uploadPostDataApi;
    }

    apiMethod(
      isNewRecord
        ? `/core/pilots/`
        : `core/pilots/${record?.handle}/`,
      infoViewActionsContext,
      formData,
    )
      .then((data: any) => {
        setRecord(data.data);
        infoViewActionsContext.showMessage(data.message);
        if (isNewRecord) {
          router.push(`/ai-identity-studio/${data.data.handle}`);
          addNewRecord(data.data);
        } else {
          updateRecord(data.data);
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const saveAgent = (agentData: any, state?: string) => {
    const formData = new FormData();
    formData.append('name', agentData?.name || '');
    formData.append('type', agentData?.type || '');
    if (agentData?.region) {
      formData.append('region', agentData?.region);
    }
    formData.append('type', agentData?.type ?? '');
    if (currentSpace?.slug) formData.append('space_slug', currentSpace?.slug);
    if (agentData?.type === 'Voice') {
      formData.append('telephony_enabled', 'true');
    }
    if (state) {
      formData.append('state', state);
    }
    updateAgentData(formData);
  };

  const getRouterPath = useMemo(() => {
    if (pathname.startsWith('/configure-agent') && currentSpace) {
      return `/configure-agent/${currentSpace.slug}`;
    }
    return `/ai-identity-studio/${record?.handle}`;
  }, [pathname, currentSpace, record]);

  if ((!record && !isNew) || isPageLoading) {
    return SkeletonView;
  }

  return (
    <StyledRoot>
      <AgentHeader
        agentData={record}
        saveAgent={saveAgent}
        loading={infoViewContext.loading}
        form={form}
      />

      <Divider style={{ margin: '0 0 5px 0' }} />
      <StyledTabsWrapper>
        <AppTabs
          items={getTabItems({
            agentData: record,
            updateAgentData,
            headerForm: form,
            agentType: record?.type,
            isNewAgent: isNewRecord,
            formatMessage,
          })}
          routePath={getRouterPath}
        />
      </StyledTabsWrapper>
    </StyledRoot>
  );
};
export default AppIdentityAgentModule;
