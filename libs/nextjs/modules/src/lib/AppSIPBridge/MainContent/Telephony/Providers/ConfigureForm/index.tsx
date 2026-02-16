import { useState } from 'react';
import { Form } from 'antd';
import {
  patchDataApi,
  postDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppLoader from '@unpod/components/common/AppLoader';
import ProviderCard from '../ProviderCard';
import { StyledRoot } from './index.styled';
import {
  convertDictionaryToList,
  convertListToDictionary,
} from '@unpod/helpers/JsonHelper';
import { AppForm } from '@unpod/components/antd';
import { useIntl } from 'react-intl';

const { useForm } = Form;

type ConfigureFormProps = {
  provider: any;
  credentials?: any;
  onCancel: () => void;
  onConfigured: (data: any) => void;
};

const ConfigureForm = ({
  provider,
  credentials,
  onCancel,
  onConfigured,
}: ConfigureFormProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [form] = useForm();
  const [loading, setLoading] = useState(false);
  const { formatMessage } = useIntl();

  const onFormSubmit = (values: any) => {
    // Prepare the configuration object
    const payload = {
      ...values,
      provider: provider.id,
      active: true,
      meta_json: values.meta_json
        ? convertListToDictionary(values.meta_json)
        : {},
    };

    if (credentials) {
      payload.id = credentials.id; // Include ID if editing existing credentials
      setLoading(true);
      // Update existing credentials
      patchDataApi(
        `telephony/provider-credentials/${credentials.id}/`,
        infoViewActionsContext,
        payload,
      )
        .then((response: any) => {
          setLoading(false);
          // Reset the form after submission
          form.resetFields();
          infoViewActionsContext.showMessage(response?.message);
          onConfigured(response?.data);
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    } else {
      postDataApi(
        'telephony/provider-credentials/',
        infoViewActionsContext,
        payload,
      )
        .then((response: any) => {
          onConfigured(response?.data);
          infoViewActionsContext.showMessage(response?.message);
          setLoading(false);
          form.resetFields();
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    }
  };

  const ProviderCardAny = ProviderCard as any;

  return (
    <StyledRoot>
      <ProviderCardAny provider={provider} hideAction />
      {provider?.form_slug && (
        <AppForm
          form={form}
          formSlug={provider.form_slug}
          onFinish={onFormSubmit}
          initialValues={
            credentials && {
              ...credentials,
              meta_json: credentials.meta_json
                ? convertDictionaryToList(credentials.meta_json)
                : [],
            }
          }
          onCancel={onCancel}
          submitBtnText={formatMessage({ id: 'bridge.verifyAndConfigure' })}
        />
      )}
      {loading && <AppLoader />}
    </StyledRoot>
  );
};

export default ConfigureForm;
