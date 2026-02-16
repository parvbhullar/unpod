import { useState } from 'react';
import { Button, Space, Tabs, Tooltip, Typography } from 'antd';
import { MdOutlineClose } from 'react-icons/md';
import { RiLinkUnlink } from 'react-icons/ri';
import { AppDrawer, AppPopconfirm } from '@unpod/components/antd';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import Providers from '../Providers';
import Config from './Config';
import Trunks from './Trunks';
import {
  StyledButton,
  StyledRoot,
  StyledTabsWrapper,
  StyledTitleContainer,
} from './index.styles';
import { useAppModuleActionsContext } from '@unpod/providers/AppModuleContextProvider';
import { useIntl } from 'react-intl';

const { Paragraph, Text } = Typography;

const getTabItems = (formatMessage: (msg: any) => string) => {
  const tabItems = [
    {
      key: 'overview',
      label: formatMessage({ id: 'bridge.settingsConfig' }),
    },
    {
      key: 'trunks',
      label: formatMessage({ id: 'bridge.settingsProviderConfig' }),
    },
  ];
  return tabItems;
};

type NumberProviderSettingsProps = {
  open: boolean;
  onClose: (open?: boolean) => void;
  sipBridge?: any;
  selectedNumber: any;
  setSelectedNumber: (value: any) => void;
  setSelectedNumbers: (updater: any) => void;
  onUnAssignConfirm: () => void;
};

const NumberProviderSettings = ({
  open,
  onClose,
  sipBridge,
  selectedNumber,
  setSelectedNumber,
  setSelectedNumbers,
  onUnAssignConfirm,
}: NumberProviderSettingsProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [openProvider, setOpenProvider] = useState(false);
  const [loading, setLoading] = useState(false);
  const { updateRecord } = useAppModuleActionsContext();
  const { formatMessage } = useIntl();

  const onLinkingSaved = (newNumber: any) => {
    setSelectedNumber(newNumber);

    setSelectedNumbers((prev: any[]) => {
      const updatedNumbers = prev.map((item: any) =>
        item.id === newNumber.id ? newNumber : item,
      );

      updateRecord({
        ...sipBridge,
        numbers: updatedNumbers,
      });

      return updatedNumbers;
    });

    if (newNumber.provider_credential) {
      setSelectedNumber(newNumber);
    } else {
      // If no provider credential, we might want to close the drawer or handle it differently
      setSelectedNumber(null);
      onClose(false);
    }
  };

  const onUnlink = () => {
    setLoading(true);

    postDataApi(
      `telephony/numbers/${selectedNumber.number_id}/unlink-provider/`,
      infoViewActionsContext,
      {},
    )
      .then((response: any) => {
        setLoading(false);
        infoViewActionsContext.showMessage(response?.message);
        onLinkingSaved({
          ...selectedNumber,
          provider_credential: null,
        });

        onClose();
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  };

  const { provider_credential } = selectedNumber || {};
  const providerName = `${provider_credential?.provider_details?.name} (${provider_credential?.name})`;

  return (
    <AppDrawer
      title={`Config - ${selectedNumber.number}`}
      open={open}
      onClose={() => onClose(false)}
      size={780}
      loading={loading}
      extra={
        <Space size={2}>
          <AppPopconfirm
            title="Unassign Number"
            description="Are you sure you want to unassign this number?"
            okText="Unassign"
            okButtonProps={{ shape: 'round' }}
            onConfirm={onUnAssignConfirm}
          >
            <Tooltip title="Unassign">
              <Button
                type="text"
                size="small"
                shape="circle"
                icon={<RiLinkUnlink fontSize={20} />}
              />
            </Tooltip>
          </AppPopconfirm>

          <Tooltip title="Close">
            <Button
              type="text"
              size="small"
              shape="circle"
              icon={<MdOutlineClose fontSize={21} />}
              onClick={() => onClose(false)}
            />
          </Tooltip>
        </Space>
      }
    >
      <StyledRoot>
        <StyledTitleContainer>
          <Text className="mb-0 bold">{providerName}</Text>

          <AppPopconfirm
            title={formatMessage({ id: 'bridge.settingsModalTitle' })}
            message={formatMessage({ id: 'bridge.settingsModalMessage' })}
            okText={formatMessage({ id: 'bridge.settingsModalText' })}
            onConfirm={onUnlink}
          >
            <StyledButton type="primary" ghost danger size="small">
              {formatMessage({ id: 'bridge.settingsModalText' })}
            </StyledButton>
          </AppPopconfirm>
        </StyledTitleContainer>

        <Paragraph className="mb-0">
          {formatMessage({ id: 'bridge.settingsDescription' })}
        </Paragraph>

        <StyledTabsWrapper>
          <Tabs
            items={getTabItems(formatMessage)}
            activeKey={activeTab}
            onChange={setActiveTab}
            tabBarStyle={{ marginBottom: 0, marginTop: 16 }}
          />

          {activeTab === 'overview' && (
            <Config
              selectedNumber={selectedNumber}
              setOpenProvider={setOpenProvider}
              setSelectedNumbers={setSelectedNumbers}
              onClose={onClose}
            />
          )}
          {activeTab === 'trunks' && <Trunks sipBridge={sipBridge} />}
        </StyledTabsWrapper>
      </StyledRoot>
      <Providers
        open={openProvider}
        onClose={() => setOpenProvider(false)}
        selectedNumber={selectedNumber}
        onLinkingSaved={onLinkingSaved}
        sipBridge={sipBridge}
      />
    </AppDrawer>
  );
};

export default NumberProviderSettings;
