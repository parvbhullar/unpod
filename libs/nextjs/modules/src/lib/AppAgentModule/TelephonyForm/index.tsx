import {useEffect, useState} from 'react';
import {Button, Flex, Form} from 'antd';
import {MdOutlinePhoneEnabled} from 'react-icons/md';
import {useGetDataApi, useInfoViewContext} from '@unpod/providers';
import CardWrapper from '@unpod/components/common/CardWrapper';
import {StickyFooter, StyledMainContainer, StyledTabRoot,} from '../index.styled';
import {SaveOutlined} from '@ant-design/icons';
import {useIntl} from 'react-intl';
import AppPhoneSelect from '@unpod/components/antd/AppPhoneSelect';
import type {Pilot, TelephonyNumber} from '@unpod/constants/types';

const {Item} = Form;

type TelephonyFormProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
};

type TelephonyFormValues = {
  phone_numbers: {
    region: string;
    numbers: string[];
  };
};

const TelephonyForm = ({agentData, updateAgentData}: TelephonyFormProps) => {
  const [region, setRegion] = useState<string>(agentData?.region || 'IN');
  const {formatMessage} = useIntl();

  const infoViewContext = useInfoViewContext();

  const [{loading, apiData: telephonyNumbers}, {setQueryParams}] =
    useGetDataApi<TelephonyNumber[]>(
      `core/telephony-numbers/`,
      {data: []},
      {type: 'agent', region: region},
      true,
    );

  useEffect(() => {
    setQueryParams({type: 'agent', region: region});
  }, [region]);

  const onFinish = (values: TelephonyFormValues) => {
    const selectedTelephonyObjects =
      telephonyNumbers?.data?.filter((item: TelephonyNumber) =>
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
              (item: TelephonyNumber) => item.number,
            ) || [],
        },
      }}
      onFinish={onFinish}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            icon={<MdOutlinePhoneEnabled/>}
            title={formatMessage({id: 'identityStudio.telephony'})}
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
                suffixIcon={<MdOutlinePhoneEnabled fontSize={16}/>}
                onChange={(val: TelephonyFormValues['phone_numbers']) => {
                  setRegion(val?.region || 'IN');
                }}
                options={telephonyNumbers?.data?.map(
                  (item: TelephonyNumber) => ({
                    key: item.number,
                    label: item.number,
                    value: item.number,
                  }),
                )}
              />
            </Item>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>
      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined/>}
            loading={infoViewContext?.loading}
          >
            {formatMessage({id: 'common.save'})}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default TelephonyForm;
