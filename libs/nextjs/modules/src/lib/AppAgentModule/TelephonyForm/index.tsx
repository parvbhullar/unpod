import { useEffect, useState } from 'react';
import { Button, Flex, Form, Select } from 'antd';
import { MdOutlinePhoneEnabled } from 'react-icons/md';
import { useGetDataApi, useInfoViewContext } from '@unpod/providers';
import CardWrapper from '@unpod/components/common/CardWrapper';
import {
  StickyFooter,
  StyledMainContainer,
  StyledTabRoot,
} from '../index.styled';
import { SaveOutlined } from '@ant-design/icons';
import { useIntl } from 'react-intl';
import AppPhoneSelect from '@unpod/components/antd/AppPhoneSelect';

const { Item } = Form;
const { Option } = Select;

type TelephonyFormProps = {
  agentData?: any;
  updateAgentData?: (data: FormData) => void;
  headerForm?: any;
};

const TelephonyForm = ({ agentData, updateAgentData }: TelephonyFormProps) => {
  const [region, setRegion] = useState(agentData?.region || 'IN');
  const { formatMessage } = useIntl();

  const infoViewContext = useInfoViewContext();

  const [{ loading, apiData: telephonyNumbers }, { setQueryParams }] =
    useGetDataApi(
      `core/telephony-numbers/`,
      { data: [] },
      { type: 'agent', region: region },
      true,
    ) as any;

  useEffect(() => {
    setQueryParams({ type: 'agent', region: region });
  }, [region]);

  const onFinish = (values: any) => {
    const selectedTelephonyObjects =
      telephonyNumbers?.data?.filter((item: any) =>
        values.phone_numbers.numbers.includes(item.number),
      ) || [];

    const formData = new FormData();
    const telephonyConfig = {
      ...agentData?.telephony_config,
      telephony: selectedTelephonyObjects,
    };

    formData.append('telephony_config', JSON.stringify(telephonyConfig));
    formData.append('region', values.phone_numbers.region || '');
    formData.append('name', agentData?.name || '');
    updateAgentData?.(formData);
  };

  return (
    <Form
      layout="vertical"
      initialValues={{
        phone_numbers: {
          region: agentData?.region || 'IN',
          numbers:
            agentData?.telephony_config?.telephony?.map(
              (item: any) => item.number,
            ) || [],
        },
      }}
      onFinish={onFinish}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            icon={<MdOutlinePhoneEnabled />}
            title={formatMessage({ id: 'identityStudio.telephony' })}
          >
            <Item
              name="phone_numbers"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.phoneNumberError',
                  }),
                },
              ]}
            >
              <AppPhoneSelect
                placeholder={formatMessage({
                  id: 'identityStudio.phoneNumberLabel',
                })}
                loading={loading}
                mode="multiple"
                suffixIcon={<MdOutlinePhoneEnabled fontSize={16} />}
                onChange={(val: any) => {
                  setRegion(val?.region || 'IN');
                }}
              >
                {telephonyNumbers?.data?.map((item: any) => (
                  <Option key={item.number} value={item.number}>
                    {item.number} {item.country && `(${item.country})`}
                  </Option>
                ))}
              </AppPhoneSelect>
            </Item>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>
      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={infoViewContext?.loading}
          >
            {formatMessage({ id: 'common.save' })}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default TelephonyForm;
