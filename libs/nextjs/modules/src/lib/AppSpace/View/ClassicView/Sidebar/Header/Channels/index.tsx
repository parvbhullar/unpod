'use client';
import type { Dispatch, SetStateAction } from 'react';
import { useEffect, useState } from 'react';
import { Button, Typography } from 'antd';
import { MdOutlineSettings } from 'react-icons/md';
import AppImage from '@unpod/components/next/AppImage';
import { useRouter } from 'next/navigation';
import { AppDrawer } from '@unpod/components/antd';
import type { Spaces } from '@unpod/constants/types';
import {
  postDataApi,
  useAuthContext,
  useFetchDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {
  StyledAddMoreRow,
  StyledAddMoreRowContent,
  StyledAppInfo,
  StyledCardContent,
  StyledCardRoot,
  StyledConnectedBadge,
  StyledConnectedChannelsContainer,
  StyledIconWrapper,
  StyledSectionWrapper,
} from './index.styles';
import { SITE_URL } from '@unpod/constants';
import { StyledRoot } from '@unpod/components/modules/AppConnectorsSetting/index.style';
import AppSettings from '@unpod/components/modules/AppConnectorsSetting/AppSettings';
import AppLoader from '@unpod/components/common/AppLoader';
import { consoleLog } from '@unpod/helpers/GlobalHelper';

const { Title, Text, Paragraph } = Typography;

type ChannelItem = {
  id?: string | number;
  app_logo?: string;
  app_name?: string;
  app_description?: string;
  app_slug?: string;
  slug?: string;
  logo?: string;
  name?: string;
  description?: string;
  url?: string;
  link_config?: unknown;
  [key: string]: unknown;
};

type ConnectedChannelProps = {
  channel: ChannelItem;
  loading: boolean;
  onSpaceUpdate: (
    payload: Record<string, unknown>,
    channel: ChannelItem,
  ) => void;
};

const ConnectedChannel = ({
  channel,
  loading,
  onSpaceUpdate,
}: ConnectedChannelProps) => {
  const [open, setOpen] = useState(false);

  return (
    <StyledCardRoot>
      <StyledCardContent>
        <StyledIconWrapper>
          <AppImage
            src={channel.app_logo || '/images/no_download.png'}
            alt={channel.app_name || 'Channel'}
            width={36}
            height={30}
          />
        </StyledIconWrapper>
        <StyledAppInfo>
          <div className="app-header">
            <Text strong>{channel.app_name}</Text>
            <div className="gear" onClick={() => setOpen(true)}>
              <MdOutlineSettings fontSize={18} />
            </div>
          </div>
          <Paragraph type="secondary" style={{ margin: 0 }}>
            {channel.app_description}
          </Paragraph>
        </StyledAppInfo>
      </StyledCardContent>
      <StyledConnectedBadge>Connected</StyledConnectedBadge>

      <AppDrawer
        title={'Channel Setting'}
        open={open}
        onClose={() => setOpen(false)}
        width={560}
      >
        <StyledRoot>
          <AppSettings connector={channel} onSettingsUpdate={onSpaceUpdate} />

          {loading && <AppLoader position="absolute" />}
        </StyledRoot>
      </AppDrawer>
    </StyledCardRoot>
  );
};

type ChannelsProps = {
  open: boolean;
  onClose: () => void;
  currentSpace: Spaces | null;
  setCurrentSpace: Dispatch<SetStateAction<Spaces | null>>;
};

const Channels = ({
  open,
  onClose,
  currentSpace,
  setCurrentSpace,
}: ChannelsProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();

  const [connectedChannels, setConnectedChannels] = useState<ChannelItem[]>([]);
  const [addMoreChannels, setAddMoreChannels] = useState<ChannelItem[]>([]);
  const [loading, setLoading] = useState(false);

  const { isAuthenticated } = useAuthContext();

  const [{ apiData }, { reCallAPI }] = useFetchDataApi(
    `channels/apps/`,
    [],
    {},
    false,
  ) as unknown as [{ apiData: ChannelItem[] }, { reCallAPI: () => void }];

  useEffect(() => {
    if (isAuthenticated) reCallAPI();
  }, [isAuthenticated]);

  useEffect(() => {
    if (apiData && apiData.length > 0) {
      const connectedApps =
        (currentSpace?.connected_apps as ChannelItem[]) ?? [];
      setConnectedChannels(connectedApps);
      setAddMoreChannels(
        apiData.filter((channel) => {
          return !connectedApps.some(
            (connected) => connected.app_slug === channel.slug,
          );
        }),
      );
    }
  }, [apiData, currentSpace?.connected_apps]);

  const onConnect = (channel: ChannelItem) => {
    if (!channel.url) return;
    const payload = {
      redirect_route: `${SITE_URL}/spaces/${currentSpace?.slug}/`,
      space: currentSpace?.slug,
      name: channel.name,
    };

    postDataApi<{ redirect_url?: string }>(
      channel.url,
      infoViewActionsContext,
      payload,
    )
      .then((response) => {
        if (response.data?.redirect_url)
          router.push(response.data.redirect_url);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onSpaceUpdate = (
    payload: Record<string, unknown>,
    channel: ChannelItem,
  ) => {
    setLoading(true);

    // API call to update connector settings
    postDataApi<{ link_config?: unknown }>(
      `channels/app-link/update-link-config/${channel.id}/`,
      infoViewActionsContext,
      payload,
    )
      .then((response) => {
        setLoading(false);
        if (response.message)
          infoViewActionsContext.showMessage(response.message);

        const connectedApps = connectedChannels.map((app) => {
          if (app.id === channel.id) {
            return {
              ...app,
              link_config: response.data?.link_config,
            };
          }

          return app;
        });

        setConnectedChannels(connectedApps);

        if (currentSpace) {
          setCurrentSpace({
            ...currentSpace,
            connected_apps: connectedApps,
          });
        }
      })
      .catch((error) => {
        setLoading(false);
        consoleLog('error', error);
        infoViewActionsContext.showError(error.message);
      });
  };

  const totalConnected = connectedChannels.length;
  const totalMoreChannels = addMoreChannels.length;

  return (
    <AppDrawer
      title="Channels"
      onClose={onClose}
      open={open}
      width={750}
      styles={{
        body: {
          backgroundColor: '#f0f0f0',
        },
      }}
    >
      <StyledSectionWrapper>
        <Title level={5}>Connected</Title>
        {totalConnected > 0 ? (
          <StyledConnectedChannelsContainer>
            {connectedChannels.map((channel, index) => (
              <ConnectedChannel
                key={index}
                channel={channel}
                loading={loading}
                onSpaceUpdate={onSpaceUpdate}
              />
            ))}
          </StyledConnectedChannelsContainer>
        ) : (
          <StyledConnectedChannelsContainer>
            <Text type="secondary">No channels connected yet.</Text>
          </StyledConnectedChannelsContainer>
        )}
      </StyledSectionWrapper>

      {totalMoreChannels > 0 && (
        <StyledSectionWrapper>
          <Title level={5}>Add More</Title>
          {addMoreChannels.map((channel, index) => (
            <StyledAddMoreRow key={index}>
              <StyledAddMoreRowContent>
                <StyledIconWrapper>
                  <AppImage
                    src={channel.logo || '/images/no_download.png'}
                    alt={channel.name || 'Channel'}
                    width={36}
                    height={36}
                  />
                </StyledIconWrapper>
                <div>
                  <Title level={5} style={{ margin: 0, marginBottom: '4px' }}>
                    {channel.name}
                  </Title>
                  <Paragraph type="secondary" style={{ margin: 0 }}>
                    {channel.description}
                  </Paragraph>
                </div>
              </StyledAddMoreRowContent>
              <Button
                type="primary"
                shape="round"
                size="small"
                onClick={() => onConnect(channel)}
                ghost
              >
                Connect
              </Button>
            </StyledAddMoreRow>
          ))}
        </StyledSectionWrapper>
      )}
    </AppDrawer>
  );
};

export default Channels;
