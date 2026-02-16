import { useEffect } from 'react';
import { Button, Form } from 'antd';
import { DrawerFooter, DrawerForm } from '@unpod/components/antd';
import {
  patchDataApi,
  useAuthActionsContext,
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import ProviderCard from '../../Providers/ProviderCard';
import { StyledRoot } from './index.styles';
import {
  convertDictionaryToList,
  convertListToDictionary,
} from '@unpod/helpers/JsonHelper';
import ProviderConfigForm from './ProviderConfigForm';
import { useIntl } from 'react-intl';

type ConfigProps = {
  selectedNumber: any;
  setOpenProvider: (open: boolean) => void;
  onClose?: (open?: boolean) => void;
  setSelectedNumbers: (updater: any) => void;
};

const Config = ({
  selectedNumber,
  setOpenProvider,
  onClose,
  setSelectedNumbers,
}: ConfigProps) => {
  const [form] = Form.useForm();
  const infoViewContext = useInfoViewContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { getSubscription } = useAuthActionsContext();
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (selectedNumber) {
      form.setFieldsValue({
        channels_count: selectedNumber?.channels_count || 1,
        agent_id: selectedNumber?.agent_id || '',
        config_json: selectedNumber?.config_json
          ? convertDictionaryToList(selectedNumber.config_json)
          : [],
      });
    }
  }, [selectedNumber, form]);

  const onConfigureSubmit = (values: any) => {
    const payload = {
      ...values,
      config_json: convertListToDictionary(values?.config_json),
    };
    patchDataApi(
      `telephony/bridge-numbers/${selectedNumber?.id}/`,
      infoViewActionsContext,
      payload,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setSelectedNumbers((prev: any[]) =>
          prev.map((item: any) =>
            item.number_id === selectedNumber.number_id
              ? { ...item, ...payload }
              : item,
          ),
        );
        getSubscription();
        onClose?.();
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const { provider_credential } = selectedNumber || {};
  const providerDetail = provider_credential?.provider_details;
  const ProviderCardAny = ProviderCard as any;

  return (
    <DrawerForm form={form} onFinish={onConfigureSubmit}>
      <StyledRoot>
        {providerDetail && (
          <ProviderCardAny
            provider={providerDetail}
            btnLabel={formatMessage({ id: 'common.manage' })}
            onButtonClick={() => setOpenProvider(true)}
            valid={provider_credential?.is_valid}
          />
        )}
        <ProviderConfigForm
          providerDetail={providerDetail}
          channelsCount={selectedNumber?.channels_count || 1}
        />
      </StyledRoot>
      <DrawerFooter>
        <Button ghost type="primary" onClick={() => onClose?.(false)}>
          {formatMessage({ id: 'common.cancel' })}
        </Button>
        <Button
          type="primary"
          htmlType="submit"
          loading={infoViewContext.loading}
        >
          {formatMessage({ id: 'common.submit' })}
        </Button>
      </DrawerFooter>
    </DrawerForm>
  );
};

export default Config;
