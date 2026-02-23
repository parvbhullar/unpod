'use client';
import {isValidElement, useEffect, useMemo} from 'react';
import {Divider, Form} from 'antd';
import {usePathname, useRouter} from 'next/navigation';
import {StyledRoot, StyledTabsWrapper} from './index.styled';
import {uploadPostDataApi, uploadPutDataApi, useInfoViewActionsContext, useInfoViewContext,} from '@unpod/providers';
import AgentHeader from './AgentHeader';
import {generateHandle} from '@unpod/helpers/StringHelper';
import {AppTabs} from '@unpod/components/antd';
import {useAppModuleActionsContext, useAppModuleContext,} from '@unpod/providers/AppModuleContextProvider';
import {AgentStudioSkeleton} from '@unpod/skeleton';
import {useSkeleton} from '@unpod/custom-hooks/useSkeleton';
import ModelForm from './ModelForm';
import VoiceForm from './VoiceForm';
import AdvancedForm from './AdvancedForm';
import AnalysisForm from './AnalysisForm';
import IntegrationForm from './IntegrationForm';
import TelephonyForm from './TelephonyForm';
import Identity from './Identity';
import {useIntl} from 'react-intl';
import type {Pilot, Spaces} from '@unpod/constants/types';

type AppAgentModuleProps = {
  pilot: Pilot;
  isNew?: boolean;
  currentSpace?: Spaces;
};

const AppAgentModule = ({
                          pilot,
                          isNew,
                          currentSpace,
                        }: AppAgentModuleProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {record, isNewRecord} = useAppModuleContext<Pilot>();
  const {setRecord, updateRecord, addNewRecord, setIsNewRecord} =
    useAppModuleActionsContext<Pilot>();
  const {formatMessage} = useIntl();

  const {isPageLoading, skeleton: Skeleton} = useSkeleton(
    AgentStudioSkeleton as any,
    AgentStudioSkeleton as any,
  );

  const infoViewContext = useInfoViewContext();
  const router = useRouter();
  const [form] = Form.useForm();
  const pathname = usePathname();

  useEffect(() => {
    if (isNew) {
      setRecord(null);
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
      const derivedPilot = {
        ...pilot,
        name: currentSpace.name,
        handle: `space-agent-${currentSpace.token}`,
      };
      setRecord(derivedPilot);
    }
  }, [pilot, currentSpace, setRecord]);

  const updateAgentData = (formData: FormData) => {
    const nameValue = String(formData.get('name') || '');
    const handleValue = record?.handle
      ? String(record.handle)
      : generateHandle(nameValue);
    formData.append('handle', handleValue);

    const apiMethod = isNewRecord ? uploadPostDataApi : uploadPutDataApi;

    apiMethod<Pilot>(
      isNewRecord ? `/core/pilots/` : `core/pilots/${record?.handle}/`,
      infoViewActionsContext,
      formData,
    )
      .then((data) => {
        setRecord(data.data);
        infoViewActionsContext.showMessage(data.message || 'Agent saved successfully');
        if (isNewRecord) {
          router.push(`/ai-studio/${data.data.handle}`);
          addNewRecord(data.data);
        } else {
          updateRecord(data.data);
        }
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const saveAgent = (agentData: Pilot, state?: string) => {
    const formData = new FormData();
    formData.append('name', agentData?.name || '');
    formData.append('type', agentData?.type || '');
    if (agentData?.region) formData.append('region', agentData?.region);
    if (currentSpace?.slug) formData.append('space_slug', currentSpace?.slug);
    if (agentData?.type === 'Voice')
      formData.append('telephony_enabled', 'true');
    if (state) formData.append('state', state);

    updateAgentData(formData);
  };

  const getRouterPath = useMemo(() => {
    if (pathname.startsWith('/configure-agent') && currentSpace) {
      return `/configure-agent/${currentSpace.slug}`;
    }
    return `/ai-studio/${record?.handle}`;
  }, [pathname, currentSpace, record]);

  const tabs = useMemo(() => {
    const items = [
      {
        key: 'identity',
        label: formatMessage({id: 'aiStudio.identity'}),
        children: (
          <Identity
            agentData={record as Pilot}
            updateAgentData={updateAgentData}
            headerForm={form}
            hideNameField={true}
          />
        ),
      },
      {
        key: 'persona',
        label: formatMessage({id: 'aiStudio.persona'}),
        disabled: isNewRecord,
        children: (
          <ModelForm
            agentData={record as Pilot}
            updateAgentData={updateAgentData}
            headerForm={form}
          />
        ),
      },
    ];

    if (record?.type === 'Voice') {
      items.push(
        {
          key: 'voice',
          label: formatMessage({id: 'aiStudio.voiceProfile'}),
          disabled: isNewRecord,
          children: (
            <VoiceForm
              agentData={record as Pilot}
              updateAgentData={updateAgentData}
              headerForm={form}
            />
          ),
        },
        {
          key: 'telephony',
          label: formatMessage({id: 'aiStudio.telephony'}),
          disabled: isNewRecord,
          children: (
            <TelephonyForm
              agentData={record as Pilot}
              updateAgentData={updateAgentData}
            />
          ),
        },
        {
          key: 'advanced',
          label: formatMessage({id: 'aiStudio.advanced'}),
          disabled: isNewRecord,
          children: (
            <AdvancedForm
              agentData={record as Pilot}
              updateAgentData={updateAgentData}
              headerForm={form}
            />
          ),
        },
        /*{
          key: 'telephony',
          label: 'Telephony',
          disabled: isNewAgent,
          children: <TelephonyForm {...restProps} />,
        }*/
      );
    }

    items.push(
      {
        key: 'analysis',
        label: formatMessage({id: 'aiStudio.analysis'}),
        disabled: isNewRecord,
        children: (
          <AnalysisForm
            agentData={record as Pilot}
            updateAgentData={updateAgentData}
            headerForm={form}
          />
        ),
      },
      {
        key: 'integration',
        label: formatMessage({id: 'aiStudio.integration'}),
        disabled: isNewRecord,
        children: (
          <IntegrationForm
            agentData={record as Pilot}
            updateAgentData={updateAgentData}
            headerForm={form}
          />
        ),
      },
    );
    return items;
  }, [record, form, formatMessage, isNewRecord, updateAgentData]);

  const SkeletonView = isValidElement(Skeleton) ? Skeleton : <Skeleton/>;

  if ((!record && !isNew) || isPageLoading) {
    return SkeletonView;
  }

  return (
    <StyledRoot>
      <AgentHeader
        agentData={record as Pilot}
        saveAgent={saveAgent}
        loading={infoViewContext.loading}
        form={form}
      />
      <Divider style={{margin: '0 0 5px 0'}}/>
      <StyledTabsWrapper>
        <AppTabs items={tabs} routePath={getRouterPath}/>
      </StyledTabsWrapper>
    </StyledRoot>
  );
};

export default AppAgentModule;
