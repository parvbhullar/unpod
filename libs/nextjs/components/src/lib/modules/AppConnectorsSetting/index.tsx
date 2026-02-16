'use client';
import { Fragment, useState } from 'react';

import { MdOutlineArrowDropDown } from 'react-icons/md';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { consoleLog } from '@unpod/helpers/GlobalHelper';
import { convertMachineNameToName } from '@unpod/helpers/StringHelper';
import AppDrawer from '../../antd/AppDrawer';
import AppSettings from './AppSettings';
import { StyledConnector, StyledConnectorTitle } from './index.style';
import { useIntl } from 'react-intl';

type ConnectedApp = {
  id: string | number;
  app_slug: string;
  link_config?: Record<string, any>;
  [key: string]: any;
};

type AppConnectorsSettingData = {
  connected_apps?: ConnectedApp[];
  [key: string]: any;};

type AppConnectorsSettingProps = {
  data?: AppConnectorsSettingData;
  setData: (data: AppConnectorsSettingData) => void;};

const AppConnectorsSetting = ({ data, setData }: AppConnectorsSettingProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [open, setOpen] = useState(false);
  const { formatMessage } = useIntl();

  const [connector] = data?.connected_apps || [];

  const onSettingsUpdate = (payload: any, connector: ConnectedApp) => {
    // API call to update connector settings
    postDataApi(
      `channels/app-link/update-link-config/${connector.id}/`,
      infoViewActionsContext,
      payload,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setData({
          ...data,
          connected_apps: (data?.connected_apps || []).map((app) => {
            if (app.id === connector.id) {
              return {
                ...app,
                link_config: response.data.link_config,
              };
            }

            return app;
          }),
        });
      })
      .catch((error: any) => {
        consoleLog('error', error);
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <Fragment>
      <StyledConnector onClick={() => setOpen(true)}>
        {/*Connected to{' '}*/}
        <StyledConnectorTitle>
          {convertMachineNameToName(connector.app_slug)}
        </StyledConnectorTitle>
        <MdOutlineArrowDropDown fontSize={20} />
      </StyledConnector>

      <AppDrawer
        title={formatMessage({ id: 'appConnectorsSetting.title' })}
        open={open}
        onClose={() => setOpen(false)}
        size={560}
        showLoader
      >
        {(data?.connected_apps || []).map((connector: ConnectedApp) => (
          <AppSettings
            key={connector.id}
            connector={connector}
            onSettingsUpdate={onSettingsUpdate}
          />
        ))}
      </AppDrawer>
    </Fragment>
  );
};

export default AppConnectorsSetting;
