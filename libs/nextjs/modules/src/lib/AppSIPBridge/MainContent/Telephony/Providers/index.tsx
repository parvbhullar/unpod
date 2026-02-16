import { useEffect } from 'react';
import { Typography } from 'antd';
import { AppDrawer } from '@unpod/components/antd';
import {
  patchDataApi,
  postDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';

import AppLoader from '@unpod/components/common/AppLoader';
import Configured from './Configured';
import NotConfigured from './NotConfigured';

import {
  IconCircleGreen,
  IconCirclePurple,
  StyledContainer,
  StyledSectionDivider,
  StyledSmallSubtext,
  StyledSubtext,
  StyledTextBlock,
  StyledTitle,
  StyledTitleContainer,
} from './index.styles';

import { MdAdd, MdOutlineSettings } from 'react-icons/md';
import { useIntl } from 'react-intl';

type ProvidersProps = {
  open: boolean;
  onClose: () => void;
  selectedNumber: any;
  sipBridge: any;
  onLinkingSaved: (number: any) => void;
};

const Providers = ({
  open,
  onClose,
  selectedNumber,
  sipBridge,
  onLinkingSaved,
}: ProvidersProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { loading } = useInfoViewContext();
  const { isAuthenticated, activeOrg } = useAuthContext();
  const { formatMessage } = useIntl();

  const [{ apiData: providerData, loading: providersLoading }] = useGetDataApi(
    `core/providers/`,
    { data: [] },
    { type: 'voice_infra' },
    isAuthenticated,
  ) as any;

  const [
    { apiData: configured, loading: configuredLoading },
    { setQueryParams, setData },
  ] = useGetDataApi(
    `telephony/provider-credentials/`,
    { data: [] },
    { type: 'voice_infra' },
    false,
  ) as any;

  useEffect(() => {
    if (isAuthenticated && activeOrg?.domain_handle) {
      setQueryParams({
        domain: activeOrg?.domain_handle,
        page: 1,
        type: 'voice_infra',
      });
    }
  }, [activeOrg, isAuthenticated]);

  const setConfigured = (data: any[]) => {
    console.log('Setting configured providers: ', data);
    setData({ data });
  };

  const onLinkNumber = (provider: any, selected: boolean) => {
    if (selected) {
      postDataApi(
        `telephony/numbers/${selectedNumber?.number_id}/unlink-provider/`,
        infoViewActionsContext,
        {},
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response?.message);
          onLinkingSaved({
            ...selectedNumber,
            provider_credential: null,
          });
          onClose();
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    } else {
      const payload = {
        provider_credential_id: provider.credentials.id,
        number_id: selectedNumber?.number_id,
      };

      const requestApiFunction = selectedNumber?.provider_details?.id
        ? patchDataApi
        : postDataApi;

      requestApiFunction(
        `telephony/bridges/${sipBridge?.slug}/numbers/`,
        infoViewActionsContext,
        payload,
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response?.message);
          if (response?.data?.provider_credential) {
            onLinkingSaved({
              ...selectedNumber,
              provider_credential: response?.data.provider_credential,
            });
          }
          onClose();
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    }
  };

  const onProviderConfigured = (provider: any) => {
    if (Array.isArray(configured.data)) {
      setConfigured([...configured.data, provider]);
    } else {
      setConfigured([provider]);
    }
  };

  const hasConfigProviders = (configured?.data || []).length > 0;

  const ConfiguredAny = Configured as any;
  const NotConfiguredAny = NotConfigured as any;

  return (
    <AppDrawer
      title={
        <>
          <StyledTitle level={4}>
            {formatMessage({ id: 'bridge.selectVoiceProviders' })}
          </StyledTitle>
          <StyledSubtext>
            {formatMessage({ id: 'bridge.selectVoiceProvidersDesc' })}
          </StyledSubtext>
        </>
      }
      onClose={onClose}
      open={open}
      width={780}
      closable
    >
      {hasConfigProviders && (
        <>
          <StyledContainer>
            <StyledTitleContainer>
              <IconCircleGreen>
                <MdOutlineSettings size={22} color="#34c759" />
              </IconCircleGreen>
              <StyledTextBlock>
                <Typography.Title level={5}>
                  {formatMessage({ id: 'bridge.activeProviders' })}
                </Typography.Title>
                <StyledSmallSubtext>
                  {formatMessage({ id: 'bridge.activeProvidersDesc' })}
                </StyledSmallSubtext>
              </StyledTextBlock>
            </StyledTitleContainer>

            <ConfiguredAny
              providers={configured?.data}
              loading={configuredLoading}
              setConfigured={setConfigured}
              onLinkNumber={onLinkNumber}
              selectedNumber={selectedNumber}
            />
          </StyledContainer>
          <StyledSectionDivider />
        </>
      )}
      <StyledContainer>
        <StyledTitleContainer>
          <IconCirclePurple>
            <MdAdd size={22} color="#8a77ff" />
          </IconCirclePurple>
          <StyledTextBlock>
            <Typography.Title level={5}>
              {formatMessage({ id: 'bridge.configure' })}
              {hasConfigProviders && formatMessage({ id: 'bridge.more' })}
            </Typography.Title>
            <StyledSmallSubtext>
              {formatMessage({
                id: hasConfigProviders
                  ? 'bridge.addMoreProviders'
                  : 'bridge.addProviders',
              })}
            </StyledSmallSubtext>
          </StyledTextBlock>
        </StyledTitleContainer>

        <NotConfiguredAny
          loading={providersLoading}
          providers={providerData?.data}
          onProviderConfigured={onProviderConfigured}
        />
      </StyledContainer>

      {loading && <AppLoader />}
    </AppDrawer>
  );
};

export default Providers;
