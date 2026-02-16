
import { Button, Divider, Form, Switch, Typography } from 'antd';
import { useIntl } from 'react-intl';
import AppInputNumber from '../../../antd/AppInputNumber';
import { StyledRoot, StyledTitleWrapper } from './index.style';

const { Title } = Typography;
const { Item } = Form;

type AppSettingsProps = {
  connector: any;
  onSettingsUpdate: (values: any, connector: any) => void;};

const AppSettings = ({ connector, onSettingsUpdate }: AppSettingsProps) => {
  const { formatMessage } = useIntl();

  return (
    <StyledRoot className="app-setting-root">
      <StyledTitleWrapper>
        <Title level={4}>
          {formatMessage(
            { id: 'appSettings.channelSetting' },
            { appName: connector.app_name },
          )}
        </Title>
      </StyledTitleWrapper>

      <Divider style={{ marginTop: 0 }} />

      <Form
        initialValues={{
          frequency: connector.link_config?.frequency || 0,
          enabled: connector.link_config?.enabled || true,
        }}
        onFinish={(values) => {
          onSettingsUpdate(values, connector);
        }}
      >
        <Item
          name="frequency"
          rules={[
            {
              required: true,
              message: formatMessage({
                id: 'appSettings.frequencyRequired',
              }),
            },
          ]}
        >
          <AppInputNumber
            placeholder={formatMessage({ id: 'appSettings.frequency' })}
          />
        </Item>

        <Item
          label={formatMessage({ id: 'appSettings.status' })}
          name="enabled"
        >
          <Switch
            checkedChildren={formatMessage({ id: 'common.enable' })}
            unCheckedChildren={formatMessage({ id: 'common.disable' })}
            size="default"
          />
        </Item>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button type="primary" shape="round" htmlType="submit">
            {formatMessage({ id: 'common.saveSettings' })}
          </Button>
        </div>
      </Form>
    </StyledRoot>
  );
};

export default AppSettings;
