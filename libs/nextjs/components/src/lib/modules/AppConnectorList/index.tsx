'use client';
import { useEffect } from 'react';
import { Typography } from 'antd';
import { useRouter } from 'next/navigation';
import {
  postDataApi,
  useAuthContext,
  useFetchDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppImage from '../../next/AppImage';
import AppLoader from '../../common/AppLoader';
import {
  StyledConnector,
  StyledConnectorProfile,
  StyledRoot,
} from './index.style';

const { Text } = Typography;

type ConnectorItem = {
  name: string;
  url: string;
  logo?: string;
  [key: string]: any;
};

type AppConnectorListProps = {
  defaultPayload?: Record<string, any>;};

const AppConnectorList = ({ defaultPayload }: AppConnectorListProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const { isAuthenticated } = useAuthContext();

  const [{ apiData, loading }, { reCallAPI }] = useFetchDataApi(
    `channels/apps/`,
    [],
    {},
    false,
  );

  useEffect(() => {
    if (isAuthenticated) reCallAPI();
  }, [isAuthenticated]);

  const onConnect = (connector: ConnectorItem) => {
    const payload = {
      ...defaultPayload,
      name: connector.name,
    };

    postDataApi(connector.url, infoViewActionsContext, payload)
      .then((response: any) => {
        router.push(response.data.redirect_url);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <StyledRoot>
      {(apiData || []).map((connector: ConnectorItem, index: number) => (
        <StyledConnector key={index} onClick={() => onConnect(connector)}>
          <StyledConnectorProfile>
            <AppImage
              src={connector.logo || ''}
              alt={connector.name || 'connector'}
              width={24}
              height={24}
            />
            <Text>{connector.name}</Text>
          </StyledConnectorProfile>
        </StyledConnector>
      ))}

      {loading && <AppLoader />}
    </StyledRoot>
  );
};

export default AppConnectorList;
