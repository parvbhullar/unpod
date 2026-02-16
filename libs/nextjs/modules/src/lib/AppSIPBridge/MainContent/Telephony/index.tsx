import { useState } from 'react';
import { Button, Form, Input, Tooltip, Typography } from 'antd';
import { MdOutlinePhone, MdOutlineSettings } from 'react-icons/md';
import AppImage from '@unpod/components/next/AppImage';
import AvailableNumbers from './AvailableNumbers';
import NumberCard from './NumberCard';
import Providers from './Providers';
import NumberProviderSettings from './NumberProviderSettings';

import {
  StyledActions,
  StyledHeading,
  StyledIconWrapper,
  StyledMainInfo,
  StyledProviderRoot,
  StyledResponsiveText,
  StyledRoot,
  StyleProviderContent,
} from './index.styled';
import AppList from '@unpod/components/common/AppList';
import { AppDrawer } from '@unpod/components/antd';
import { useAppModuleActionsContext } from '@unpod/providers/AppModuleContextProvider';
import AppWarningTooltip from '@unpod/components/common/AppWarningLabel';
import { useAuthActionsContext } from '@unpod/providers';
import { StyledDescContainer } from '../BridgeHeader/index.styled';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Title, Paragraph } = Typography;

type TelephonyProps = {
  sipBridge?: any;
  selectedNumbers?: any[];
  setSelectedNumbers: (numbers: any[]) => void;
  saveBridgeData?: (payload: any, callback?: any) => void;
  headerRef?: { current?: { form?: any } };
};

type BridgeNumber = {
  id?: string | number;
  number_id?: string | number;
  provider_credential?: any;
  [key: string]: any;
};

const Telephony = ({
  sipBridge,
  selectedNumbers = [],
  setSelectedNumbers,
  saveBridgeData,
  headerRef,
}: TelephonyProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [openProvider, setOpenProvider] = useState(false);
  const [openSettings, setOpenSettings] = useState(false);
  const [selectedNumber, setSelectedNumber] = useState<BridgeNumber | null>(
    null,
  );
  const [editDescInput, setEditDescInput] = useState(false);
  const { updateRecord } = useAppModuleActionsContext();
  const { getSubscription } = useAuthActionsContext();
  const form = (headerRef?.current?.form as any) || ({} as any);
  const { formatMessage } = useIntl();

  const onSelectionDone = (
    newNumbers: BridgeNumber[],
    callBackFun: () => void,
  ) => {
    if (saveBridgeData) {
      saveBridgeData(
        {
          numberIds: newNumbers.map((number) => number.number_id || number.id),
        },
        () => {
          setIsOpen(false);
          setSelectedNumbers(newNumbers);
          callBackFun();
          getSubscription();
        },
      );
    }
  };

  const onDeleteNumber = (number: BridgeNumber) => {
    const numbers = selectedNumbers.filter(
      (item: BridgeNumber) => item.number_id !== number.number_id,
    );

    if (saveBridgeData) {
      saveBridgeData(
        { numberIds: numbers.map((number: BridgeNumber) => number.number_id) },
        getSubscription,
      );
    }
  };

  const onUnAssignConfirm = () => {
    if (!selectedNumber) return;
    const numbers = selectedNumbers.filter(
      (item: BridgeNumber) => item.number_id !== selectedNumber.number_id,
    );
    setSelectedNumber(null);
    setOpenSettings(false);

    // If saveBridgeData is provided, call it with the new numbers
    if (saveBridgeData) {
      saveBridgeData(
        { numberIds: numbers.map((number: BridgeNumber) => number.number_id) },
        getSubscription,
      );
    }
  };

  const onProviderSelect = (item: BridgeNumber) => {
    setOpenProvider(true);
    setSelectedNumber(item);
  };

  const onLinkingSaved = (newNumber: BridgeNumber) => {
    setSelectedNumber(newNumber);
    const numbers = selectedNumbers.map((item: BridgeNumber) =>
      item.id === newNumber.id ? newNumber : item,
    );

    setSelectedNumbers(numbers);

    updateRecord({ ...sipBridge, numbers });
  };

  const onNumberSettings = (number: BridgeNumber) => {
    setSelectedNumber(number);
    setOpenSettings(true);
  };

  const onSaveData = (callback?: (payload: any, error?: any) => void) => {
    form
      .validateFields()
      .then(() => {
        const payload = {
          description: form.getFieldValue('description') || '',
          numberIds: selectedNumbers.map(
            (number: BridgeNumber) => number.number_id || number.id,
          ),
        };

        saveBridgeData?.(payload);
        setEditDescInput(false);
        callback?.(payload, null);
      })
      .catch(() => {
        callback?.(null, { error: true });
      });
  };

  return (
    <StyledRoot>
      <Form
        form={form}
        initialValues={sipBridge}
        onFinish={() => onSaveData(sipBridge?.status)}
      >
        <StyledDescContainer>
          {sipBridge?.description && !editDescInput ? (
            <Paragraph
              style={{ margin: 0 }}
              onClick={() => setEditDescInput(true)}
            >
              {sipBridge?.description}
            </Paragraph>
          ) : (
            <Form.Item name="description" noStyle>
              <Input.TextArea
                placeholder={formatMessage({
                  id: 'bridge.bridgeDescriptionPlaceholder',
                })}
                style={{ width: '100%' }}
                autoSize={{ minRows: 1, maxRows: 5 }}
              />
            </Form.Item>
          )}
        </StyledDescContainer>
      </Form>
      <StyledMainInfo>
        <StyledHeading level={5}>
          {formatMessage({ id: 'bridge.telephonyConfig' })}
        </StyledHeading>
        <Paragraph>{formatMessage({ id: 'bridge.telephonyDesc' })}</Paragraph>
      </StyledMainInfo>

      <StyledActions>
        <Button
          type="primary"
          icon={<MdOutlinePhone fontSize={18} />}
          onClick={() => setIsOpen(true)}
          ghost
        >
          {formatMessage({ id: 'bridge.selectNumber' })}
        </Button>
      </StyledActions>

      {selectedNumbers.length > 0 && (
        <>
          <Title
            style={{
              marginTop: 12,
              marginBottom: -4,
            }}
            level={5}
          >
            {formatMessage({ id: 'bridge.selectedNumbers' })}
          </Title>
          <AppList
            data={selectedNumbers}
            renderItem={(item: BridgeNumber, index: number) => {
              const { provider_credential } = item;
              const providerName = provider_credential?.provider_details
                ? ``
                : formatMessage({ id: 'bridge.notLinked' });
              return (
                <NumberCard
                  key={index}
                  item={item}
                  providerName={providerName}
                  btnLabel={formatMessage({ id: 'bridge.configure' })}
                  ProviderProfile={
                    provider_credential && (
                      <ProviderProfile
                        number={item}
                        onClick={() => onNumberSettings(item)}
                      />
                    )
                  }
                  onClick={() => onProviderSelect(item)}
                  onDeleteClick={onDeleteNumber}
                  selected={false}
                  selectedBtnLabel={formatMessage({ id: 'common.unselect' })}
                  hideAvailable
                />
              );
            }}
          />
        </>
      )}

      <AppDrawer
        title={formatMessage({ id: 'bridge.availableNumbers' })}
        open={isOpen}
        onClose={() => setIsOpen(false)}
        size={600}
        showLoader
      >
        <AvailableNumbers
          open={isOpen}
          onClose={() => setIsOpen(false)}
          selectedNumbers={selectedNumbers}
          onSelectionDone={onSelectionDone}
        />
      </AppDrawer>

      <Providers
        open={openProvider}
        onClose={() => setOpenProvider(false)}
        selectedNumber={selectedNumber}
        onLinkingSaved={onLinkingSaved}
        sipBridge={sipBridge}
      />

      {selectedNumber && (
        <NumberProviderSettings
          open={openSettings}
          onClose={() => setOpenSettings(false)}
          sipBridge={sipBridge}
          selectedNumber={selectedNumber}
          setSelectedNumber={setSelectedNumber}
          setSelectedNumbers={setSelectedNumbers}
          onUnAssignConfirm={onUnAssignConfirm}
        />
      )}
    </StyledRoot>
  );
};

const ProviderProfile = ({
  number,
  onClick,
}: {
  number: BridgeNumber;
  onClick: () => void;
}) => {
  const { provider_credential } = number || {};
  if (!provider_credential?.provider_details) return null;
  const providerName = `${provider_credential.provider_details.name} (${provider_credential.name})`;
  const valid = provider_credential?.is_valid;
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const { formatMessage } = useIntl();

  return (
    <StyledProviderRoot>
      <StyleProviderContent>
        <StyledIconWrapper>
          <AppImage
            src={provider_credential.provider_details.icon}
            alt={providerName}
            width={24}
            height={24}
          />
        </StyledIconWrapper>

        <StyledResponsiveText className="mb-0">
          {providerName}
        </StyledResponsiveText>
      </StyleProviderContent>

      {!valid && (
        <AppWarningTooltip
          style={{
            marginRight: -8,
          }}
        />
      )}
      <Tooltip title={formatMessage({ id: 'common.settings' })}>
        <Button
          type={mobileScreen ? 'default' : 'text'}
          shape="circle"
          size="small"
          icon={<MdOutlineSettings fontSize={18} />}
          onClick={onClick}
        />
      </Tooltip>
    </StyledProviderRoot>
  );
};

export default Telephony;
