import { Button, Col, Form, Row, Typography } from 'antd';
import { MdAdd, MdDelete } from 'react-icons/md';
import { AppInput, AppInputNumber } from '@unpod/components/antd';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { StyledItemRow } from './index.styles';
import AgentSelectField from './AgentSelectField';
import { useAuthContext } from '@unpod/providers';
import { getSubscriptionModule } from '@unpod/helpers/PaymentHelper';
import { useIntl } from 'react-intl';

const { Item, List } = Form;
const { Paragraph } = Typography;

const ProviderConfigForm = ({
  providerDetail,
  channelsCount,
}: {
  providerDetail: any;
  channelsCount: number;
}) => {
  const providerName = providerDetail?.name?.toLowerCase();
  const { subscription } = useAuthContext();
  const usageData = getSubscriptionModule(
    (subscription as any)?.modules,
    'channels',
  ) as any;
  const remaining = usageData?.remaining || 0;
  const selectChannels = Form.useWatch(['channels_count']);
  const form = Form.useFormInstance();
  const { formatMessage } = useIntl();

  return (
    <>
      <Row gutter={[12, 16]}>
        <Col sm={24} lg={11}>
          <Form.Item
            name="channels_count"
            validateTrigger="onChange"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'bridge.concurrencyRequired' }),
              },
              () => ({
                validator(_, value) {
                  if (value > remaining + channelsCount) {
                    return Promise.reject(
                      new Error(
                        formatMessage(
                          { id: 'bridge.maxChannelsAllowed' },
                          { count: remaining + channelsCount },
                        ),
                      ),
                    );
                  }
                  return Promise.resolve();
                },
              }),
            ]}
            help={
              selectChannels && selectChannels > remaining + channelsCount
                ? formatMessage(
                    { id: 'bridge.maxChannelsHelp' },
                    { count: remaining + channelsCount },
                  )
                : formatMessage(
                    { id: 'bridge.channelsHelp' },
                    {
                      total: remaining + channelsCount,
                      remain: remaining,
                    },
                  )
            }
          >
            <AppInputNumber
              placeholder={formatMessage({
                id: 'bridge.concurrencyPlaceholder',
              })}
              min={1}
              max={remaining + channelsCount}
              step={1}
            />
          </Form.Item>
        </Col>
        <Col sm={24} lg={13}>
          <Form.Item
            name="agent_id"
            rules={[
              {
                required: providerName !== 'vapi',
                message: formatMessage({ id: 'bridge.agentRequired' }),
              },
            ]}
          >
            {providerName == 'unpod.ai' ? (
              <AgentSelectField />
            ) : (
              <AppInput
                placeholder={formatMessage({
                  id:
                    providerName === 'vapi'
                      ? 'bridge.enterVapiAgentId'
                      : 'bridge.enterAgent',
                })}
              />
            )}
          </Form.Item>
        </Col>
      </Row>
      <Paragraph style={{ marginBottom: 0 }}>
        {formatMessage({ id: 'bridge.configFields' })}
      </Paragraph>
      <List name="config_json">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <StyledItemRow key={key}>
                <Item
                  {...restField}
                  name={[name, 'key']}
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'validation.fieldRequired',
                      }),
                    },
                  ]}
                >
                  <AppInput
                    placeholder={formatMessage({
                      id: 'bridge.keyPlaceholder',
                    })}
                    onBlur={(event: any) => {
                      const configKey = event.target.value;

                      if (configKey) {
                        const formattedKey = getMachineName(configKey);
                        const items = form.getFieldValue('config_json');
                        items[name].key = formattedKey;
                        form.setFieldsValue({ config_json: items });
                      }
                    }}
                    asterisk
                  />
                </Item>

                <Item
                  {...restField}
                  name={[name, 'value']}
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'validation.fieldRequired',
                      }),
                    },
                  ]}
                >
                  <AppInput
                    placeholder={formatMessage({
                      id: 'bridge.valuePlaceholder',
                    })}
                    asterisk
                  />
                </Item>

                <Item>
                  <Button
                    type="primary"
                    onClick={() => remove(name)}
                    icon={<MdDelete fontSize={18} />}
                    danger
                    ghost
                  />
                </Item>
              </StyledItemRow>
            ))}

            <Item>
              <Button
                type="dashed"
                onClick={() => add()}
                block
                icon={<MdAdd />}
              >
                {formatMessage({ id: 'common.addField' })}
              </Button>
            </Item>
          </>
        )}
      </List>
    </>
  );
};

export default ProviderConfigForm;
